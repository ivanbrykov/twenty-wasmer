let compare: typeof import('./bcrypt-compat.util').compare;
let hash: typeof import('./bcrypt-compat.util').hash;

const fixtures = [
  {
    name: 'ascii',
    password: 'synthetic-password',
    hash: '$2b$04$......................2VBaBohsKe8kgA1pDEkLBJ7N/fpMWfC',
  },
  {
    name: 'oauth-secret',
    password:
      '0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef',
    hash: '$2b$04$......................pUYahbvaOEJTxtvZotpzwH/aup0t9hm',
  },
  {
    name: 'unicode',
    password: 'Cr\u00e8me-\u79d8\u5bc6-\ud83d\udd12',
    hash: '$2b$04$......................bJy0YdG5ZSz/oQUGv.4kNAJ13hT1dyW',
  },
  {
    name: 'unicode-nfd',
    password: 'e\u0301-password',
    hash: '$2b$04$......................5Pm1pg.ejxuR3uO3G6CHLewc7JvzLNK',
  },
  {
    name: 'nul',
    password: 'test\u0000password',
    hash: '$2b$04$......................nYY/H1OzM1UOtZC7dHe/v0pcLnTuDUq',
  },
  {
    name: 'empty',
    password: '',
    hash: '$2b$04$......................w74bL5gU7LSJClZClCa.Pkz14aTv/XO',
  },
  {
    name: '71-bytes',
    password:
      'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa',
    hash: '$2b$04$......................OKajFstSaQgvFOLFT26yIEg4fPr47jO',
  },
  {
    name: '72-bytes',
    password:
      'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa',
    hash: '$2b$04$......................UaUp2CqHXn14N7RprrzoDsNv91ahi36',
  },
  {
    name: '73-bytes',
    password:
      'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa',
    hash: '$2b$04$......................UaUp2CqHXn14N7RprrzoDsNv91ahi36',
  },
  {
    name: 'unicode-over-72',
    password:
      '\ud83d\udd12\ud83d\udd12\ud83d\udd12\ud83d\udd12\ud83d\udd12\ud83d\udd12\ud83d\udd12\ud83d\udd12\ud83d\udd12\ud83d\udd12\ud83d\udd12\ud83d\udd12\ud83d\udd12\ud83d\udd12\ud83d\udd12\ud83d\udd12\ud83d\udd12\ud83d\udd12\ud83d\udd12\ud83d\udd12\ud83d\udd12\ud83d\udd12\ud83d\udd12\ud83d\udd12\ud83d\udd12',
    hash: '$2b$04$......................aAWShVEGbhlIS5oT2i5mk8syMucc5WS',
  },
  {
    name: 'split-utf8-boundary',
    password:
      'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa\u00e9',
    hash: '$2b$04$......................k.hsIl4FrHiFJvMwpb41B3GKgu/zOEq',
  },
];

describe('bcrypt compatibility adapter', () => {
  beforeAll(async () => {
    jest.useRealTimers();
    ({ compare, hash } = await import('./bcrypt-compat.util'));
  });
  afterAll(() => jest.useFakeTimers());
  it.each(fixtures)(
    'verifies native hashes: $name',
    async ({ password, hash: encoded }) => {
      await expect(compare(password, encoded)).resolves.toBe(true);
      await expect(
        compare(password, encoded.replace('$2b$', '$2a$')),
      ).resolves.toBe(true);
      const first = Array.from(password)[0] ?? '';
      const wrong = (first === 'X' ? 'Y' : 'X') + password.slice(first.length);
      await expect(compare(wrong, encoded)).resolves.toBe(false);
    },
  );

  it.each(fixtures)('round trips fresh hashes: $name', async ({ password }) => {
    const encoded = await hash(password, 4);
    await expect(compare(password, encoded)).resolves.toBe(true);
  });

  it('uses independent random salts and preserves the requested cost', async () => {
    const first = await hash('synthetic-password', 10);
    const second = await hash('synthetic-password', 10);
    expect(first).not.toBe(second);
    expect(first).toMatch(/^\$2[ab]\$10\$/);
    await expect(compare('synthetic-password', first)).resolves.toBe(true);
  });

  it.each([
    '',
    'invalid',
    '$2y$04$' + '.'.repeat(53),
    '$2b$03$' + '.'.repeat(53),
  ])('rejects malformed or unsupported hash: %s', async (encoded) => {
    await expect(compare('synthetic-password', encoded)).resolves.toBe(false);
  });

  it.each([0, 3, 32, 4.5, Number.NaN])(
    'rejects invalid cost %s',
    async (cost) => {
      await expect(hash('synthetic-password', cost)).rejects.toThrow(
        RangeError,
      );
    },
  );
});
