import base64
import sys


def main():
    if len(sys.argv) < 3:
        print("Usage: python crypt_auth.py <input_file> <output_file>")
        print("Example: python crypt_auth.py auth.txt auth.enc")
        sys.exit(1)

    in_file = sys.argv[1]
    out_file = sys.argv[2]
    key = "ZAI_FARM_OBFUSCATION"

    try:
        with open(in_file, "r", encoding="utf-8") as f:
            data = f.read().strip() + "\n"

        # Simple XOR Encrypt
        encrypted_xor = "".join(
            chr(ord(c) ^ ord(key[i % len(key)])) for i, c in enumerate(data)
        )
        # Base64 Encode to make it safe to store in text/git
        encrypted_b64 = base64.b64encode(encrypted_xor.encode("utf-8")).decode("utf-8")

        with open(out_file, "w", encoding="utf-8") as f:
            f.write(encrypted_b64)

        print(f"Success! Encrypted '{in_file}' to '{out_file}'")
        print(f"You can now safely commit '{out_file}' and delete '{in_file}'.")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
