# Speeding Up Evidence Synthesis for Conservation

This is the Github Repository for the Part IB CS Project "Speeding Up Evidence Synthesis for Conservation". Based on a Dataset from the Department of Zoology, we have designed a regression model that labels Papers as relevant for Conservation Research on a decimal scale. 

This Project consists of a Flask based UI, a live data pipeline, a Transformer based ML model and deployment using Nvidia NGC and docker compose.

The data pipeline uses publicly available APIs from (CORE, Crossref, Arxiv and Semanticscholar) to fetch new articles on the fly (Data Scraper). We have bootstrapped the Sqlite Database originally with the Semanticscholar database dump. The department of Zoology gave us a set of relevant articles (~30k) for which we fetched abstracts on which we performed the analysis. To give the model negative samples, we took random articles mixed with articles from similar issues that were not selected.

The current best performance model is based on Tranfer Learning from DistilledBert. F1 score was 90% for the working model.

# Set Up

Setting this project up on a local machine can be rather hard. First, you need to ensure that your system has NVIDIA and CUDA drivers installed - then you need to ensure that you support nvidia docker (NGC) - to get access to the docker image you will need an NVIDIA account and verify yourself with docker. Furthermore, the image requires a linux operating system at the moment. I tested it on Ubuntu 18.

If you want access to our data, you can contact me directly via github and we can arrange a data exchange and if you need help with the installation, feel free to contact me.

(The project does not come with the data, so it will crash when trying to access the databases.)
