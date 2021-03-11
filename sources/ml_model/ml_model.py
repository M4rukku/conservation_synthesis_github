from sources.data_processing.queries import ArticleMetadata


class MlModelWrapper:
    """The interface that needs to be implemented by the MLModel.

    CURRENTLY having problems with integration! So dummy classifier is used.
    """    
    def __init__(self, classifier=None):
        #self.classifier = PytorchModel()
        pass


    def predict_article(self, article: ArticleMetadata) -> bool:
        """Predicts the relevance of an article based on its abstract.

        Args:
            article (ArticleMetadata): The article to be judged.

        Returns:
            bool: True if relevant, False otherwise.
        """
        return False
        #return self.classifier.do_prediction(article.title, article.journal_name, article.abstract)
