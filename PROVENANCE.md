# Provenance

This repository was written from scratch in October 2026 as a clean-room demonstration of
Python automation skills the author has applied in data-protection operations work: REST
authentication, paginated listing of jobs/sources, storage statistics, tenant-level usage
(chargeback-style) reporting and CSV export.

Only the *concepts* were carried over. No code, data, configuration, hostnames, credentials,
reports, customer or employer material, vendor SDK code, or third-party scripts were copied
or adapted. The REST contract used here (`/api/v1/jobs`, cursor pagination, etc.) is invented
for illustration and is not the Cohesity API. Everything is licensed under Apache-2.0.
