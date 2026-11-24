# Local-only derivation from the already verified successful C1 candidate image.
# It intentionally keeps a private make copy and removes /usr/bin/make so the
# DRAFT baseline still fails with MISSING_MAKE while the derived candidate can
# restore make without apt or Docker Hub access.
FROM e6-draft-replay:e1774f5f38f5440b8ccfc41618ceec47-2
RUN mkdir -p /opt/offline-toolchain \
 && cp /usr/bin/make /opt/offline-toolchain/make \
 && rm -f /usr/bin/make /usr/bin/gmake
