from sources.data_processing.queries import ArticleMetadata

class MlModelWrapper:
    """The interface that needs to be implemented by the MLModel.
    """    
    def __init__(self, classifier=None):
        self.classifier = classifier

    def predict_article(self, article: ArticleMetadata) -> bool:
        """Predicts the relevance of an article based on its abstract.

        Args:
            article (ArticleMetadata): The article to be judged.

        Returns:
            bool: True if relevant, 0 otherwise.
        """        
        return False
