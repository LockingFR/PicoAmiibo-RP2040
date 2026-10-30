# Preserved empty firmware

The original local backup set is ignored by Git:
backups/manager-v1-20261030/prototype-p1 and prototype-p2. Every listed file was
reread and SHA256-verified before Manager development. No private amiibo is
embedded in these UF2 files.

- **0.1.1/P1**, original local source 1cba4c5:
  SHA256 bc71827d0893e1dd9090493484c70d258fb8d0132c6bf440111269d1b4902329.
  Delivery preceding the user-reported Epona result.
- **0.1.2/P2**, original local source 35d1d42:
  SHA256 f518a2744dbb83ebb29e23b275aa91e9cacd36a656ce112ebb7b4896f77b07c9.
  No L+R gesture; console qualification pending.

The application never flashes them automatically. A firmware update may preserve
existing tag banks; an empty factory image is not an instruction to wipe storage.

## Fresh source builds

Manager builds do not require these ignored historical backup files. If the
verified local backup set is available, the packager includes the two separate
recovery folders. Otherwise, it packages the app and documents without recovery
UF2s. Download the separately labeled images and checksums from GitHub Releases
when recovery is needed. The checked-in C source builds 0.1.2, not the older 0.1.1.
