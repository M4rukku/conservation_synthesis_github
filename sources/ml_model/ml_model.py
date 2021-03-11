from sources.data_processing.queries import ArticleMetadata
from sources.ml_model.pytorch_model import PytorchModel


class MlModelWrapper:
    """The interface that needs to be implemented by the MLModel.
    """    
    def __init__(self, classifier=None):
        self.classifier = PytorchModel()


    def predict_article(self, article: ArticleMetadata) -> bool:
        """Predicts the relevance of an article based on its abstract.

        Args:
            article (ArticleMetadata): The article to be judged.

        Returns:
            bool: True if relevant, False otherwise.
        """
        return self.classifier.do_prediction(article.title, article.journal_name, article.abstract)
