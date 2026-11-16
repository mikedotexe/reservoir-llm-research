# Notarizing the research integration app

November 16, 2026: **not submitted**. The Mac reports zero valid signing identities;
Apple signing/notarization environment variables are absent, and this repository's
Actions secret inventory is empty. The qualified 0.54.0 ZIP remains ad-hoc signed.

Install a **Developer ID Application** certificate with its matching private key
in the local keychain. Configure `APPLE_SIGNING_IDENTITY` with that identity's full
name. Supply either `APPLE_ID`, `APPLE_TEAM_ID`, and an **app-specific**
`APPLE_PASSWORD`, or the App Store Connect API variables documented by Tauri.
Keep credentials local; do not put them in chat, the repository, or command logs.
[Tauri signing and notarization](https://v2.tauri.app/distribute/sign/macos/)
· [Apple Developer ID certificates](https://developer.apple.com/help/account/certificates/create-developer-id-certificates).

Once the owner has configured the Apple ID credential option, run from
`desktop/ReservoirScope`. These commands have **not** been executed with an Apple
identity. They build a separate release bundle, preserving the qualified debug app.

```sh
security find-identity -v -p codesigning
: "${APPLE_SIGNING_IDENTITY:?Set the installed Developer ID Application identity}"
: "${APPLE_ID:?Configure the Apple account locally}"
: "${APPLE_TEAM_ID:?Configure the Apple team locally}"
: "${APPLE_PASSWORD:?Configure an app-specific password locally}"
PYTHON=/opt/homebrew/bin/python3.14 npm run tauri build -- \
  --config src-tauri/tauri.research-api.conf.json --bundles app
```

Tauri uses these credentials for signing and notarization. Preserve its submission
ID and result. Require Apple acceptance and successful ticket validation before
calling the replacement notarized:

```sh
codesign --verify --deep --strict 'target/release/bundle/macos/Reservoir Research Integration.app'
xcrun stapler validate 'target/release/bundle/macos/Reservoir Research Integration.app'
spctl --assess --type execute --verbose=2 'target/release/bundle/macos/Reservoir Research Integration.app'
```

Apple distinguishes acceptance from attaching the ticket to the delivered app;
preserve both results. See [Apple's notarization workflow](https://developer.apple.com/documentation/security/customizing-the-notarization-workflow).

Then repeat the isolated API and extracted-package qualification for the signed
binary, including OS URL navigation. Update the package's actual signing/build
identity and README, produce a new archive/checksum/receipt, and preserve the old
package. The current local packager labels its output as a debug, ad-hoc build;
do not reuse that label for a release signed with Developer ID. No replacement of
the three ongoing experiments is implied by signing or source publication.

Documentation lookup used official Tauri/Apple sources because the requested
Mintlify index context tool was unavailable in this session.
