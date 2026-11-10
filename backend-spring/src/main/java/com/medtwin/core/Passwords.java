package com.medtwin.core;

import javax.crypto.SecretKeyFactory;
import javax.crypto.spec.PBEKeySpec;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.SecureRandom;
import java.util.Base64;

/** Reads and writes Django's pbkdf2_sha256 / pbkdf2_sha1 hashes so existing accounts keep working. */
public final class Passwords {
    private static final int ITERATIONS = 600000;
    private static final int KEY_LENGTH = 256;
    private static final String ALPHABET =
            "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789";

    private Passwords() {
    }

    public static boolean matches(String raw, String encoded) {
        if (encoded == null) return false;
        String[] parts = encoded.split("\\$");
        if (parts.length != 4) return false;
        String algorithm = parts[0].equals("pbkdf2_sha256")
                ? "PBKDF2WithHmacSHA256"
                : parts[0].equals("pbkdf2_sha1") ? "PBKDF2WithHmacSHA1" : null;
        if (algorithm == null) return false;
        try {
            int iterations = Integer.parseInt(parts[1]);
            byte[] expected = Base64.getDecoder().decode(parts[3]);
            byte[] actual = derive(algorithm, raw, parts[2].getBytes(StandardCharsets.UTF_8),
                    iterations, expected.length * 8);
            return MessageDigest.isEqual(expected, actual);
        } catch (Exception exc) {
            return false;
        }
    }

    public static String encode(String raw) {
        SecureRandom random = new SecureRandom();
        StringBuilder salt = new StringBuilder();
        for (int i = 0; i < 12; i++) salt.append(ALPHABET.charAt(random.nextInt(ALPHABET.length())));
        byte[] hash = derive("PBKDF2WithHmacSHA256", raw,
                salt.toString().getBytes(StandardCharsets.UTF_8), ITERATIONS, KEY_LENGTH);
        return "pbkdf2_sha256$" + ITERATIONS + "$" + salt + "$"
                + Base64.getEncoder().encodeToString(hash);
    }

    private static byte[] derive(String algorithm, String raw, byte[] salt, int iterations, int bits) {
        try {
            PBEKeySpec spec = new PBEKeySpec(raw.toCharArray(), salt, iterations, bits);
            return SecretKeyFactory.getInstance(algorithm).generateSecret(spec).getEncoded();
        } catch (Exception exc) {
            throw new IllegalStateException(exc);
        }
    }
}
