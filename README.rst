Panoptes
========

Runs a Firefox instance on the cloud, and display a dashboard
with its metrics.


Long-run scenario:

- Start Firefox
- Visit url
- Collect data for one hour
- Discard five first minutes
- Compute linear regression for each metrics
- Compute activity level

Linear regression in 10 minutes slices
wait until it gets flat
if not check that it's steadily growing
alert
