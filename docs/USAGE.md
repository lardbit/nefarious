# Usage

## Finding content to download

- click **Search** from the main menu
- select either **Movies** or **TV**
- enter your query
- click the matching title

## Downloading Movies

- change **Quality Profile** if you want to update the default setting
- click the **Watch** button and nefarious will begin searching and downloading the movie

### Manually searching for Movies

Sometimes you want more control about what torrent is chosen for download.

*Only admin users will see this option*.

- click the **Manual Search** tab to begin a torrent search
- sort the results as necessary (i.e. by name, seeders, size)
- click the *download* icon and nefarious will download that torrent and associate that movie with it

## Downloading TV

### Watch Every Season

- click the **Watch all seasons** button and nefarious will begin searching and downloading every season

### Watch an Entire Season

- click the button next to the season you want and nefarious will begin searching and downloading that season

### Watch Specific Episodes in a Season

- expand the season you want and check the specific episodes you want and nefarious will begin searching for and downloading those episodes

### Manually searching for TV

Sometimes you want more control about which torrent is chosen for download.

*Only admin users will see this option*.

- expand the season you want
- click the **Manual** checkbox
- click the *search* icon next to a specific episode or the entire season button
- sort the results as necessary (i.e. by name, seeders, size)
- click the *download* icon and nefarious will download that torrent and associate that show with it

## Checking Download Status

- click the **Status** tab to see the progress (whether a torrent was found, and, if so, how much has been downloaded)

## Blacklist & Retry a torrent

Sometimes a movie or tv show you download may be too low quality, wrong match, wrong sub-titles, or just completely fake.
You can tell nefarious to blacklist & delete that torrent and search again to find the next best option.

- click the **Status** tab on a movie or tv show
- click the *Blacklist and Retry* icon

## Importing existing libraries

If you have existing TV and Movie libraries, nefarious can import them for you.
Go to the *Settings* page and you'll see the **Import Library** section.  The process will be in the background and can take
a while depending on the size of your libraries.

If you want to see the logs you can run:

    docker-compose logs -f celery

## Notifications

nefarious can send notifications (e.g. push notifications, email, sms) when media is downloaded.   
See [Apprise](https://github.com/caronc/apprise) for documentation on how to construct the *Notification Url* for
the [available notification services](https://github.com/caronc/apprise#popular-notification-services).

Enter the *Notification Url* on the settings page.  You can test it from there to make sure it works as expected.

Something like: `slack://TokenA/TokenB/TokenC/`

You'll receive a notification everytime new media is downloaded.
