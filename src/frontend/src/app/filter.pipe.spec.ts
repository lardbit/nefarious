import { MediaFilterPipe } from './filter.pipe';

describe('MediaFilterPipe', () => {
  let pipe: MediaFilterPipe;

  beforeEach(() => {
    pipe = new MediaFilterPipe();
  });

  it('should return all items if search is empty', () => {
    const items = [{ title: 'A' }, { title: 'B' }];
    expect(pipe.transform(items, '')).toEqual(items);
  });

  it('should return all items if search is null', () => {
    const items = [{ title: 'A' }];
    expect(pipe.transform(items, null as any)).toEqual(items);
  });

  it('should return all items if search is undefined', () => {
    const items = [{ title: 'A' }];
    expect(pipe.transform(items, undefined as any)).toEqual(items);
  });

  it('should filter items by title field (case insensitive)', () => {
    const items = [
      { title: 'Breaking Bad' },
      { title: 'Better Call Saul' },
      { title: 'The Wire' },
    ];
    const result = pipe.transform(items, 'break');
    expect(result.length).toBe(1);
    expect(result[0].title).toBe('Breaking Bad');
  });

  it('should filter items by Title (capital T) field', () => {
    const items = [
      { Title: 'Inception' },
      { Title: 'Interstellar' },
    ];
    const result = pipe.transform(items, 'interstellar');
    expect(result.length).toBe(1);
    expect(result[0].Title).toBe('Interstellar');
  });

  it('should filter items by name field', () => {
    const items = [
      { name: 'The Matrix' },
      { name: 'The Godfather' },
    ];
    const result = pipe.transform(items, 'god');
    expect(result.length).toBe(1);
  });

  it('should filter items by release_date field', () => {
    const items = [
      { release_date: '2020-01-15' },
      { release_date: '2021-06-20' },
    ];
    const result = pipe.transform(items, '2020');
    expect(result.length).toBe(1);
    expect(result[0].release_date).toBe('2020-01-15');
  });

  it('should return empty array when no items match', () => {
    const items = [
      { title: 'Stranger Things' },
    ];
    const result = pipe.transform(items, 'zzzz');
    expect(result).toEqual([]);
  });

  it('should trim search string', () => {
    const items = [
      { title: 'Dark' },
    ];
    const result = pipe.transform(items, '  Dark  ');
    expect(result.length).toBe(1);
  });

  it('should handle empty items array', () => {
    const result = pipe.transform([], 'test');
    expect(result).toEqual([]);
  });
});
