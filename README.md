# Speeding Up Evidence Synthesis for Conservation

This is the Github Repository for the Part IB CS Project "Speeding Up Evidence Synthesis for Conservation". Based on a Dataset from the Department of Zoology, we have designed a regression model that labels Papers as relevant for Conservation Research on a decimal scale. 

This Project consists of a Flask based UI, a live data pipeline, a Transformer based ML model and deployment using Nvidia NGC and docker compose.

The data pipeline uses publicly available APIs from (CORE, Crossref, Arxiv and Semanticscholar) to fetch new articles on the fly (Data Scraper). We have bootstrapped the Sqlite Database originally with the Semanticscholar database dump. The department of Zoology gave us a set of relevant articles (~30k) for which we fetched abstracts on which we performed the analysis. To give the model negative samples, we took random articles mixed with articles from similar issues that were not selected.

The current best performance model is based on Tranfer Learning from DistilledBert. F1 score was 90% for the working model.
