#!/usr/bin/env python3
"""
Generate unique WASM files by adding custom sections with unique data.
Each generated file will have a different SHA256 hash.
"""


import os
import sys
import hashlib
import struct


def read_wasm(path):
    with open(path, 'rb') as f:
        return bytearray(f.read())


def write_wasm(path, data):
    with open(path, 'wb') as f:
        f.write(data)


def create_custom_section(name, data):
    """Create a custom section (id=0) with given name and data."""
    name_bytes = name.encode('utf-8')
    name_len = len(name_bytes)


    # Section content: name_len (LEB128) + name + data
    content = bytes([name_len]) + name_bytes + data
    content_len = len(content)


    # Encode content length as LEB128
    leb128_len = []
    val = content_len
    while True:
        byte = val & 0x7f
        val >>= 7
        if val != 0:
            byte |= 0x80
        leb128_len.append(byte)
        if val == 0:
            break


    # Section: id (0) + length (LEB128) + content
    return bytes([0]) + bytes(leb128_len) + content


def add_custom_section(wasm_data, section_data):
    """Add a custom section after the WASM header (first 8 bytes)."""
    header = wasm_data[:8]  # WASM magic + version
    rest = wasm_data[8:]
    return header + section_data + rest


def generate_unique_wasm(source_path, output_dir, count, prefix="unique"):
    """Generate 'count' unique WASM files from source."""


    if not os.path.exists(output_dir):
        os.makedirs(output_dir)


    source_data = read_wasm(source_path)
    manifest = []


    for i in range(1, count + 1):
        # Generate unique data using random bytes
        unique_data = os.urandom(32) + struct.pack('<I', i)


        # Create custom section with unique data
        custom_section = create_custom_section(f"unique_{i}", unique_data)


        # Add custom section to WASM
        new_wasm = add_custom_section(source_data, custom_section)


        # Calculate hash for verification
        file_hash = hashlib.sha256(bytes(new_wasm)).hexdigest()


        # Save file
        output_filename = f"{prefix}_{i:05d}.wasm"
        output_path = os.path.join(output_dir, output_filename)
        write_wasm(output_path, new_wasm)


        manifest.append((output_path, file_hash))


        if i % 100 == 0:
            print(f"Generated {i}/{count} files...")


    # Write manifest
    manifest_path = os.path.join(output_dir, "manifest.txt")
    with open(manifest_path, 'w') as f:
        for path, hash_val in manifest:
            f.write(f"{path}\t{hash_val}\n")


    print(f"Generated {count} unique WASM files in {output_dir}")
    print(f"Manifest written to {manifest_path}")


    return manifest


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: generate_unique_wasm.py <source.wasm> <output_dir> <count> [prefix]")
        sys.exit(1)


    source = sys.argv[1]
    output_dir = sys.argv[2]
    count = int(sys.argv[3])
    prefix = sys.argv[4] if len(sys.argv) > 4 else "unique"


    generate_unique_wasm(source, output_dir, count, prefix)
