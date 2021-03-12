# Speeding Up Evidence Synthesis for Conservation

This is the current version of our project. Working Frontend integrated with the backend and the data scraper. Deployment using Nvidia NGC and docker compose.

The current best performance model (DistilledBert) is not integrated with the backend since we had a hardware mismatch (it was trained on a cluster with multiple GPUs) and the export didn't work as is. We will try to fix it soon, sadly the model locked behind multiple firewalls (so Jamie has to make a second physical appearance at the cluster). F1 score was 90%! for the working model which we are very happy with.

We will fix the integration for our client by next week.
