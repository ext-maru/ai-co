"""
    pygments.lexers._cocoa_builtins
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This file defines a set of types used across Cocoa frameworks from Apple.
    There is a list of @interfaces, @protocols and some other (structs, unions)

    File may be also used as standalone generator for above.

    :copyright: Copyright 2006-2025 by the Pygments team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

if __name__ == '__main__':  # pragma: no cover:
    import os
    import re

    FRAMEWORKS_PATH = '/Applications/Xcode.app/Contents/Developer/Platforms/iPhoneOS.platform/Developer/SDKs/iPhoneOS.sdk/System/Library/Frameworks/'
    frameworks = os.listdir(FRAMEWORKS_PATH)

    all_interfaces = set()
    all_protocols  = set()
    all_primitives = set()
    for framework in frameworks:
        frameworkHeadersDir = FRAMEWORKS_PATH + framework + '/Headers/'
        if not os.path.exists(frameworkHeadersDir):
            continue

        headerFilenames = os.listdir(frameworkHeadersDir)

        for f in headerFilenames:
            if not f.endswith('.h'):
                continue
            headerFilePath = frameworkHeadersDir + f
                
            try:
                with open(headerFilePath, encoding='utf-8') as f:
                    content = f.read()
            except UnicodeDecodeError:
                print(f"Decoding error for file: {headerFilePath}")
                continue
                
            res = re.findall(r'(?<=@interface )\w+', content)
            for r in res:
                all_interfaces.add(r)

            res = re.findall(r'(?<=@protocol )\w+', content)
            for r in res:
                all_protocols.add(r)

            res = re.findall(r'(?<=typedef enum )\w+', content)
            for r in res:
                all_primitives.add(r)

            res = re.findall(r'(?<=typedef struct )\w+', content)
            for r in res:
                all_primitives.add(r)

            res = re.findall(r'(?<=typedef const struct )\w+', content)
            for r in res:
                all_primitives.add(r)

    print("ALL interfaces: \n")
    print(sorted(list(all_interfaces)))

    print("\nALL protocols: \n")
    print(sorted(list(all_protocols)))

    print("\nALL primitives: \n")
    print(sorted(list(all_primitives)))
