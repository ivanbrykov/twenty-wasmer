import { randomBytes } from 'crypto';

import * as bcryptJs from 'bcryptjs';
import { bcrypt, bcryptVerify } from 'hash-wasm';

// This adapter covers Twenty's string-based hash/compare calls, not bcrypt's
// complete API. Retain the native binding's byte truncation and hash formats.
const NATIVE_HASH_PATTERN =
  /^\$2[ab]\$(0[4-9]|[12][0-9]|3[01])\$[./A-Za-z0-9]{53}$/;

const passwordBytes = (password: string): Buffer => {
  if (typeof password !== 'string') {
    throw new TypeError('Password must be a string');
  }

  return Buffer.from(password, 'utf8').subarray(0, 72);
};

const needsJsFallback = (bytes: Buffer): boolean =>
  bytes.length === 0 || bytes.includes(0);

export const hash = async (
  password: string,
  rounds: number,
): Promise<string> => {
  const bytes = passwordBytes(password);

  if (!Number.isInteger(rounds) || rounds < 4 || rounds > 31) {
    throw new RangeError('Bcrypt rounds must be an integer between 4 and 31');
  }

  // hash-wasm differs on empty/NUL inputs; bcryptjs preserves native behavior.
  if (needsJsFallback(bytes)) {
    return bcryptJs.hash(password, rounds);
  }

  return bcrypt({
    password: bytes,
    salt: randomBytes(16),
    costFactor: rounds,
    outputType: 'encoded',
  });
};

export const compare = async (
  password: string,
  passwordHash: string,
): Promise<boolean> => {
  const bytes = passwordBytes(password);

  if (typeof passwordHash !== 'string') {
    throw new TypeError('Password hash must be a string');
  }

  // Native bcrypt rejects unsupported/malformed hashes. Do not delegate those
  // to a library that accepts additional prefixes or throws on malformed input.
  if (!NATIVE_HASH_PATTERN.test(passwordHash)) {
    return false;
  }

  if (needsJsFallback(bytes)) {
    return bcryptJs.compare(password, passwordHash);
  }

  return bcryptVerify({ password: bytes, hash: passwordHash });
};
