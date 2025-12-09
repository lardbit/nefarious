import requests
from django.conf import settings
from nefarious.tmdb import get_tmdb_client
from typing import Optional, List
from langchain_openai import ChatOpenAI
from langchain_core.tools import StructuredTool
from langchain.agents import create_agent
from pydantic import BaseModel, Field


# structured response
class MovieInfo(BaseModel):
    title: str = Field(description="The title of the movie")
    tmdb_id: int = Field(description="The TMDB ID of the movie")
    release_year: str = Field(description="The release year of the movie")
    overview: str = Field(description="A brief summary of the movie")
    streaming_providers: Optional[List[str]] = Field(description="List of providers if known, otherwise empty")


# structured response
class MovieResponse(BaseModel):
    """Structured response containing a list of movies found and a summary."""
    movies: List[MovieInfo] = Field(description="List of movies matching the user's criteria")
    summary: str = Field(description="A natural language summary of what was found")


class Agent:

    def __init__(self, nefarious_settings):
        self.nefarious_settings = nefarious_settings
        self.tmdb_client = get_tmdb_client(nefarious_settings)

    def _search_person_id(self, name: str) -> str:
        """
        Searches for a person (actor, director, etc.) by name and returns their TMDB ID.
        Use this to find the 'id' needed for 'with_cast' or 'with_crew' filters.
        """
        try:
            search = self.tmdb_client.Search()
            response = search.person(query=name)
            if response['results']:
                # Return the first (most likely) result
                person = response['results'][0]
                return f"ID: {person['id']} (Name: {person['name']})"
            return f"No person found for '{name}'"
        except Exception as e:
            return f"Error searching for person: {str(e)}"

    def _search_keyword_id(self, topic: str) -> str:
        """
        Searches for a topic/keyword by text and returns the TMDB ID.
        Use this to translate user topics (e.g., "time travel", "aliens") into IDs
        needed for the 'with_keywords' filter.
        """
        try:
            search = self.tmdb_client.Search()
            response = search.keyword(query=topic)
            if response['results']:
                # Return the first result
                keyword = response['results'][0]
                return f"ID: {keyword['id']} (Name: {keyword['name']})"
            return f"No keyword found for '{topic}'"
        except Exception as e:
            return f"Error searching for keyword: {str(e)}"

    def _search_genre_id(self, genre_name: str) -> str:
        """
        Searches for a movie genre by name (e.g., 'Action', 'Comedy') and returns its ID.
        """
        try:
            genres = self.tmdb_client.Genres()
            response = genres.movie_list()
            for g in response['genres']:
                if g['name'].lower() == genre_name.lower():
                    return f"ID: {g['id']} (Name: {g['name']})"
            return f"No genre found for '{genre_name}'"
        except Exception as e:
            return f"Error: {str(e)}"

    def _search_provider_id(provider_name: str) -> str:
        """
        Searches for a streaming provider (e.g., 'Netflix', 'Hulu') and returns its ID.
        Needed for filtering by where a movie is streaming.
        """
        try:
            # tmdbsimple doesn't have a direct method for this list in older versions,
            # so we hit the endpoint directly.
            url = f"https://api.themoviedb.org/3/watch/providers/movie?api_key={settings.TMDB_API_TOKEN}&language=en-US&watch_region=US"
            response = requests.get(url)
            if response.status_code == 200:
                results = response.json().get('results', [])
                for provider in results:
                    if provider_name.lower() in provider['provider_name'].lower():
                        return f"ID: {provider['provider_id']} (Name: {provider['provider_name']})"
                return f"No provider found for '{provider_name}'"
            return f"Error fetching providers: {response.status_code}"
        except Exception as e:
            return f"Error: {str(e)}"

    def _discover_movies(
            self,
            cast_ids: Optional[str] = None,
            keyword_ids: Optional[str] = None,
            genre_ids: Optional[str] = None,
            provider_ids: Optional[str] = None,
            certification: Optional[str] = None,
            year: Optional[int] = None,
            sort_by: str = "popularity.desc"
    ) -> str:
        """
        Finds movies using powerful filters.

        CRITICAL INSTRUCTIONS FOR LOGIC:
        - 'cast_ids', 'keyword_ids', 'genre_ids', 'provider_ids':
          - Use comma (,) for AND logic (e.g., "123,456" means BOTH must be present).
          - Use pipe (|) for OR logic (e.g., "123|456" means EITHER can be present).

        ARGS:
        - cast_ids: List of person IDs.
        - keyword_ids: List of keyword IDs.
        - genre_ids: List of genre IDs.
        - provider_ids: List of watch provider IDs (e.g. Netflix ID).
        - certification: 'R', 'PG-13', etc. (Assumes US region).
        - year: Primary release year (integer).
        """
        try:
            discover = self.tmdb_client.Discover()

            kwargs = {
                'sort_by': sort_by,
                'include_adult': False,
                'page': 1
            }

            if cast_ids: kwargs['with_cast'] = cast_ids
            if keyword_ids: kwargs['with_keywords'] = keyword_ids
            if genre_ids: kwargs['with_genres'] = genre_ids

            # Watch Providers logic
            if provider_ids:
                kwargs['with_watch_providers'] = provider_ids
                kwargs['watch_region'] = 'US'  # Required when using watch providers

            # Certification logic
            if certification:
                kwargs['certification_country'] = 'US'
                kwargs['certification'] = certification

            if year:
                kwargs['primary_release_year'] = year

            response = discover.movie(**kwargs)
            results = response['results']

            if not results:
                return "No movies found matching these criteria."

            # Return a structured string for the LLM to parse into the final response format
            formatted_results = []
            for movie in results[:10]:  # Increased limit to 10
                formatted_results.append(
                    f"ID: {movie.get('id')}, "
                    f"Title: {movie.get('title')}, "
                    f"Year: {movie.get('release_date', '')[:4]}, "
                    f"Overview: {movie.get('overview', '')[:100]}..."
                )

            return "\n".join(formatted_results)

        except Exception as e:
            return f"Error discovering movies: {str(e)}"

    def _build_agent(self):

        # initialize the LLM
        llm = ChatOpenAI(
            model=self.nefarious_settings.ai_model,
            base_url=self.nefarious_settings.ai_base_url,
            temperature=0,
            api_key=self.nefarious_settings.ai_api_key,
        )

        # define the tool list
        tools = [
            StructuredTool.from_function(
                func=self._search_person_id,
                name="search_person_id",
                description=self._search_person_id.__doc__,
            ),
            StructuredTool.from_function(
                func=self._search_keyword_id,
                name="search_keyword_id",
                description=self._search_keyword_id.__doc__,
            ),
            StructuredTool.from_function(
                func=self._discover_movies,
                name="discover_movies",
                description=self._discover_movies.__doc__,
            ),
            StructuredTool.from_function(
                func=self._search_genre_id,
                name="search_genre_id",
                description=self._search_genre_id.__doc__,
            ),
            StructuredTool.from_function(
                func=self._search_provider_id,
                name="search_provider_id",
                description=self._search_provider_id.__doc__,
            ),
        ]

        # define system prompt
        system_prompt = (
            "You are an advanced movie scout agent. "
            "Your goal is to find movies that perfectly match the user's detailed criteria.\n\n"
            "RULES:\n"
            "1. Always search for IDs first (Person, Keyword, Genre, Provider). Do not guess IDs.\n"
            "2. LOGIC: If a user says 'Action AND Comedy', use a comma (,) in the discover tool.\n"
            "   If a user says 'Action OR Comedy', use a pipe (|) in the discover tool.\n"
            "   This applies to Cast, Genres, Keywords, and Providers.\n"
            "3. If filtering by streaming provider, assume US region.\n"
            "4. Return the final answer in the structured format provided."
        )

        # construct the agent (graph)
        graph = create_agent(
            llm,
            tools,
            system_prompt=system_prompt,
            response_format=MovieResponse,
        )

        return graph

    def query(self, query: str):
        agent = self._build_agent()
        inputs = {"messages": [("user", query)]}
        result = agent.invoke(inputs)
        structured_data = result.get("structured_response")
        return [dict(result) for result in structured_data.movies]
