# ckan-pycsw


GitHub Releases [Changelog](https://github.com/mjanez/ckan-pycsw/releases)

<!-- insertion marker -->
## v2.6.1 - 2025-10-30

<small>[Compare with latest](https://github.com/mjanez/ckan-pycsw/compare/v2.6.1...HEAD)</small>

### Added

- Add JSON ([cd54d40](https://github.com/mjanez/ckan-pycsw/commit/cd54d40844a9c92fedd9e7bf17ce6b94b42746c4) by mjanez).
- Add retry mechanism for HTTP requests and update dependencies ([60df19d](https://github.com/mjanez/ckan-pycsw/commit/60df19d0b84b1d8bcc5b0f3c89fb4ac01fb95aff) by mjanez).
- Add PYCSW catalog configuration to Dockerfile.dev ([f9a2cb8](https://github.com/mjanez/ckan-pycsw/commit/f9a2cb897c9b27d5c7a828cd30bad544ccea28de) by mjanez).
- Add Changelog file ([c922f0f](https://github.com/mjanez/ckan-pycsw/commit/c922f0f8d1d005e421c00a27c042f9d4a2b63496) by mjanez).
- Add dockers to testing ([fdd68b9](https://github.com/mjanez/ckan-pycsw/commit/fdd68b967dd1d4db96e58099e243d257760781a2) by mjanez).
- Add multilang first version ([8abd23c](https://github.com/mjanez/ckan-pycsw/commit/8abd23c5b825a477ff39dfa3a3dc358e5302f236) by mjanez).
- Add matrix to docker action ([9b5b4ee](https://github.com/mjanez/ckan-pycsw/commit/9b5b4ee501002307d76565169cee4358c132f7e9) by mjanez).
- Add main to docker-pr ([38878ca](https://github.com/mjanez/ckan-pycsw/commit/38878ca7401c11cc6a940c6c6c4bd7d483740524) by mjanez).
- Add trivy scan ([93b5fad](https://github.com/mjanez/ckan-pycsw/commit/93b5fadd417362b53e784443a442ee84b798f427) by mjanez).
- Add non-root user to images ([770bfef](https://github.com/mjanez/ckan-pycsw/commit/770bfefbaad918db0314cc87277fde0b445140a0) by mjanez).
- Add scan & lint to docker actions ([4b48d64](https://github.com/mjanez/ckan-pycsw/commit/4b48d642103da7ea8fd48fcaef1c80fc1d329914) by mjanez).
- Add dockerfile scan to actions ([4232b4f](https://github.com/mjanez/ckan-pycsw/commit/4232b4fbd9a06759b7d5e9de8322452c53347b1b) by mjanez).
- Add README.md to log/ and metadata/ ([fc4ee51](https://github.com/mjanez/ckan-pycsw/commit/fc4ee5147e44f3f393947c1d52108ea1cc90d01d) by mjanez).
- Add cronjob & fix json lists ([169248d](https://github.com/mjanez/ckan-pycsw/commit/169248de5a3f67e0158c8fb183984fd5922dcf54) by mjanez).
- Add info to README ([882f4c1](https://github.com/mjanez/ckan-pycsw/commit/882f4c145de35db25fed87757cf5969c3bfb40be) by mjanez).
- Add image types to README ([878374c](https://github.com/mjanez/ckan-pycsw/commit/878374cd55d56a7772cdedb851bd26f3923d1de3) by mjanez).
- Add unlicense ([b9aa40c](https://github.com/mjanez/ckan-pycsw/commit/b9aa40cb6403f6541ffef48e8e7b63fbe3ff2aa3) by mjanez).
- Add wait-for ([7b58b58](https://github.com/mjanez/ckan-pycsw/commit/7b58b5852e77bbbaf3574536c753b6a57f05b7fa) by Francesco Frassinelli).
- Add gmd:contact/gmd:CI_ResponsibleParty ([8bca430](https://github.com/mjanez/ckan-pycsw/commit/8bca43055a33f9fc9a64ac18bbae24d7c6a158ac) by Francesco Frassinelli).
- Add distributor contact ([700afc5](https://github.com/mjanez/ckan-pycsw/commit/700afc512e57699f9f6ee60037fe06829e80bd86) by Francesco Frassinelli).
- Add healthcheck ([7d01c0b](https://github.com/mjanez/ckan-pycsw/commit/7d01c0b977dc8f4aa4c56106a37868a1c3a47d96) by Francesco Frassinelli).
- Add README.md ([97b7395](https://github.com/mjanez/ckan-pycsw/commit/97b7395cb761735a3880b79994c37e51f3c44f58) by Francesco Frassinelli).
- Add docker-compose.yml ([f385bad](https://github.com/mjanez/ckan-pycsw/commit/f385badb53381af35fe7ec430b64d1ac38c219d2) by Francesco Frassinelli).
- Add GitHub actions ([3584c75](https://github.com/mjanez/ckan-pycsw/commit/3584c75b2c6f07098d7789f374acb94593dac10a) by Francesco Frassinelli).

### Fixed

- Fix docker.yaml ([62ee2ac](https://github.com/mjanez/ckan-pycsw/commit/62ee2accfb141dfb9fd3d84ac795742309b1b9f3) by mjanez).
- Fix CKAN_SYSADMIN_EMAIL ([636ce52](https://github.com/mjanez/ckan-pycsw/commit/636ce52bf9581d699a9fef43c964e04c7c7bebad) by mjanez).
- Fix publisher contact variable and enrich ISO19139 INSPIRE template with author/distributor, purpose/credit, HVD keywords/categories, and resource constraints ([f24392d](https://github.com/mjanez/ckan-pycsw/commit/f24392d03377271deae7c806c642a527e1137b7a) by mjanez).
- Fix APP_DIR default, correct PYCSW_OUTPUT_SCHEMA typo, and re-enable ptvsd dev attach ([f527492](https://github.com/mjanez/ckan-pycsw/commit/f527492df8f361421e2c4373899cb7171046b556) by mjanez).
- Fix env vars and Docker setup ([c4dc65b](https://github.com/mjanez/ckan-pycsw/commit/c4dc65ba08eeac3c6f0255a75666e93379757897) by mjanez).
- Fix JSON deserialization error in render_j2_template function ([8f3af39](https://github.com/mjanez/ckan-pycsw/commit/8f3af397bd06c7af685c5a81ef2f093da2916c86) by mjanez).
- Fix notes ([314a86c](https://github.com/mjanez/ckan-pycsw/commit/314a86ccdaf4d7238c3e012dff237d1c1eb667ab) by mjanez).
- Fix bugs when DEV_MODE is None ([5b4075e](https://github.com/mjanez/ckan-pycsw/commit/5b4075e64ed89e662bcdc939e678a79409d384d9) by mjanez).
- Fix ckan dataset retrieving ([2a5ca63](https://github.com/mjanez/ckan-pycsw/commit/2a5ca63e8bc17bb1e82c5d5998ab4b692fabef9b) by mjanez).
- Fix ghcr Dockerfile ([2da1c0f](https://github.com/mjanez/ckan-pycsw/commit/2da1c0f4aa3ae995261ac75e93b4738c7e5a2ac1) by mjanez).
- Fix permissions to mount volumes ([11f7097](https://github.com/mjanez/ckan-pycsw/commit/11f7097b19741666d79d61f48ff0f18e5cc25eac) by mjanez).
- Fix temp warning of debug ([806f8a8](https://github.com/mjanez/ckan-pycsw/commit/806f8a8400ed6bfa8b8ab9ab3ad04b37b02c7186) by mjanez).
- Fix docker-pr action ([71584a1](https://github.com/mjanez/ckan-pycsw/commit/71584a114092e1da22efe88e380436d9770aad95) by mjanez).
- Fix metadata actions ([0744939](https://github.com/mjanez/ckan-pycsw/commit/0744939fc068ddb983e89a9ed46922aaf8c613b6) by mjanez).
- Fix docker actions ([ca629b9](https://github.com/mjanez/ckan-pycsw/commit/ca629b9c8297dcde3742d0aa470a1140b0de5cae) by mjanez).
- Fix docker build & push ([48ef746](https://github.com/mjanez/ckan-pycsw/commit/48ef7463d0cc312a93e6009dff48eba3d7c5da2a) by mjanez).
- Fix workflow ([ae728d0](https://github.com/mjanez/ckan-pycsw/commit/ae728d0a48e0dfef19639894dc0b90905d1d7f84) by mjanez).
- Fix actions and Dockerfiles ([e559d41](https://github.com/mjanez/ckan-pycsw/commit/e559d4181c0fca6501f9387480c6219e66fec371) by mjanez).
- Fix actions to avoid fail and push info to PR ([d8bc5e8](https://github.com/mjanez/ckan-pycsw/commit/d8bc5e88cdf48b22576d3df9fa39545e3c226a28) by mjanez).
- Fix Dockerfile lint ([33033c4](https://github.com/mjanez/ckan-pycsw/commit/33033c40a20e09f914806284e09dfe9bdfd5281e) by mjanez).
- Fix PR action ([60926be](https://github.com/mjanez/ckan-pycsw/commit/60926be3760751aa53b8dd281465f63f17cdd35a) by mjanez).
- Fix PR actions ([0315a3c](https://github.com/mjanez/ckan-pycsw/commit/0315a3c9fad1be137645625a860feb014e3d41db) by mjanez).
- Fix actions to avoid sha instead of tag ([a6e81b9](https://github.com/mjanez/ckan-pycsw/commit/a6e81b98117ed0c2b2359de0abda154852b37069) by mjanez).
- Fix RUN apt-get ([ff8a060](https://github.com/mjanez/ckan-pycsw/commit/ff8a0608492f398a1a71a0d0e9d816c15ea7b192) by mjanez).
- Fix Dockerfile lint errors/warnings/info ([72d7e45](https://github.com/mjanez/ckan-pycsw/commit/72d7e451a2f329b20315efaefd204db9f9c7b344) by mjanez).
- Fix actions ([d60b620](https://github.com/mjanez/ckan-pycsw/commit/d60b620c2205502c369931d6112896ed9f9f94f0) by mjanez).
- Fix permissions ([8b65463](https://github.com/mjanez/ckan-pycsw/commit/8b65463f780974329b6ae0fb79f2134295984e7a) by mjanez).
- Fix COPY with more than 2 arguments requires the last argument to end with / ([74835ef](https://github.com/mjanez/ckan-pycsw/commit/74835ef19781564bba713a5c1c7e78165270b32b) by mjanez).
- Fix context/paths of actions ([117b3a4](https://github.com/mjanez/ckan-pycsw/commit/117b3a430a95bd8a4e331abeb2411de4fbd7b010) by mjanez).
- Fix context/dockerfile of actions ([0da7716](https://github.com/mjanez/ckan-pycsw/commit/0da7716d964be71bf3bb1b64e406371dbba0b201) by mjanez).
- Fix scan image ([607a8e3](https://github.com/mjanez/ckan-pycsw/commit/607a8e34b6b09afb28cecdca06537d4a3b3d0f4e) by mjanez).
- Fix README ([a3ae7bd](https://github.com/mjanez/ckan-pycsw/commit/a3ae7bde1f08b1c2fdfae3cc9bce600fcd490ee7) by mjanez).
- Fix identifier ([dfddd42](https://github.com/mjanez/ckan-pycsw/commit/dfddd420a89a98bfab9ad173b1df0e6ca2fcd19b) by mjanez).
- Fix cronjobs by use scheduler ([6dc5a78](https://github.com/mjanez/ckan-pycsw/commit/6dc5a78bbbe256f898607aeba852ff5a1ae9e670) by mjanez).
- Fix cronjobs ([bac35c6](https://github.com/mjanez/ckan-pycsw/commit/bac35c6d338474642f67c6c4d214b56fb3e1735d) by mjanez).
- Fix cite ([214dad1](https://github.com/mjanez/ckan-pycsw/commit/214dad1b81f0a3ec098c65715ce822fb39c331e0) by mjanez).
- Fix errors and update logging info ([95500a7](https://github.com/mjanez/ckan-pycsw/commit/95500a7f30d2da61739567a90b8771c51b93ff00) by mjanez).
- Fix CRLF to LF ([f720fb9](https://github.com/mjanez/ckan-pycsw/commit/f720fb9924a68c9b07f46da9a7bc78082f910aa5) by mjanez).
- Fix docker compose ([dc92b72](https://github.com/mjanez/ckan-pycsw/commit/dc92b72a797978338e4c495779bf07645be0f8d5) by mjanez).
- Fix image/repo name ([cbd6106](https://github.com/mjanez/ckan-pycsw/commit/cbd6106258598d232d1e369eae7718df936c4ae1) by mjanez).
- Fix distribution and URLs ([9887908](https://github.com/mjanez/ckan-pycsw/commit/98879081730142eb9d8641f4b2609051227effcd) by Francesco Frassinelli).
- Fix contact individualname ([bad9703](https://github.com/mjanez/ckan-pycsw/commit/bad970356a9a2bfeef4390394dea3131c2e656fc) by Francesco Frassinelli).

### Changed

- Change default PYCSW_URL ([d488b83](https://github.com/mjanez/ckan-pycsw/commit/d488b83bbcd65c49b9bca6a217cc6efd14f2a19f) by Francesco Frassinelli).

### Removed

- Remove platform ([a8aa173](https://github.com/mjanez/ckan-pycsw/commit/a8aa173764bb339e7795702251e1cab0ef3c8b51) by mjanez).
- Remove jobs an use independent workflows ([fe7806f](https://github.com/mjanez/ckan-pycsw/commit/fe7806f79b3b032e9ecc10672de260c4d9c2f0df) by mjanez).
- Remove package dev ([3ca55f1](https://github.com/mjanez/ckan-pycsw/commit/3ca55f1a7f5de0a469df1cc3ab2ab6d2e54b8269) by mjanez).
- Remove draft folder ([cd3be3f](https://github.com/mjanez/ckan-pycsw/commit/cd3be3f206ad4d97a599b2a4a78e09c7f29e8d1c) by mjanez).
- Remove snyk and use docker lint ([a7c9e4c](https://github.com/mjanez/ckan-pycsw/commit/a7c9e4c081b321e0e9d00f2867085e8b6dbda417) by mjanez).
- Remove unused logging ([4135c70](https://github.com/mjanez/ckan-pycsw/commit/4135c700cbd943800b9d7a2b4aff04d5e54a1374) by mjanez).
- Remove gmd:spatialRepresentationInfo ([7694f94](https://github.com/mjanez/ckan-pycsw/commit/7694f940837cb99aeb4267d9f11d3bf44aaa770c) by mjanez).
- Remove unused code ([97bd24e](https://github.com/mjanez/ckan-pycsw/commit/97bd24e0332e3fd55e338951ca9a345f643b29c5) by mjanez).

<!-- insertion marker -->
