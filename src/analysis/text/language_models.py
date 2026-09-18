"""Phase 6: Profile Language Patterns, Differential TF-IDF, and LDA Topic Modeling.

- Extracts unigrams & bigrams from combined profile text using TF-IDF.
- Computes Differential TF-IDF (Log-Odds Ratio / score difference) between high-earners and non-high-earners.
- Fits Latent Dirichlet Allocation (LDA) topic model.
- Analyzes topic distribution across earnings tiers and assigns dominant topic per user.
- Outputs `data/analytical/text_terms.parquet` and `data/analytical/topics.parquet`.
"""

import re
from typing import Any

import duckdb
import numpy as np
import pandas as pd
from loguru import logger
from sklearn.decomposition import LatentDirichletAllocation
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer

from src.common.config import DEFAULT_CONFIG, PipelineConfig

# Custom domain stopwords to filter generic freelancer boilerplate
CUSTOM_STOPWORDS = {
    "will",
    "can",
    "work",
    "experience",
    "years",
    "services",
    "client",
    "clients",
    "project",
    "projects",
    "provide",
    "quality",
    "time",
    "best",
    "also",
    "good",
    "looking",
    "looking for",
    "help",
    "need",
    "like",
    "great",
    "job",
    "high",
    "satisfaction",
    "guaranteed",
    "freelancer",
    "freelance",
    "expert",
    "professional",
    "work with",
    "years of",
    "feel free",
    "free to",
    "contact me",
    "get in",
    "in touch",
    "let know",
    "day day",
    "etc",
    "hello",
    "hi",
    "thanks",
    "thank you",
    "welcome",
}


def _clean_text(text: str) -> str:
    """Cleans and tokenizes text."""
    if not isinstance(text, str):
        return ""
    text = text.lower()
    text = re.sub(r"https?://\S+|www\.\S+", "", text)
    text = re.sub(r"[^a-z0-9\s#+\.\-]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


class ProfileTextAnalyzer:
    """Analyzes freelancer profile text using TF-IDF and LDA."""

    def __init__(self, config: PipelineConfig = DEFAULT_CONFIG):
        self.config = config

    def load_corpus(self) -> tuple[pd.DataFrame, pd.Series, np.ndarray]:
        con = duckdb.connect()
        query = f"""
        SELECT 
            f.user_id,
            f.high_earner,
            f.total_earnings,
            f.log_earnings,
            t.combined_text
        FROM read_parquet('{self.config.freelancers_parquet}') f
        JOIN read_parquet('{self.config.profile_text_parquet}') t ON f.user_id = t.user_id
        ORDER BY f.user_id
        """
        df = con.execute(query).fetchdf()
        con.close()

        logger.info(f"Loaded {len(df)} profile texts for language analysis.")
        cleaned_series = df["combined_text"].fillna("").apply(_clean_text)
        is_high_earner = df["high_earner"].to_numpy(dtype=bool)
        return df, cleaned_series, is_high_earner

    def compute_differential_tfidf(
        self,
        cleaned_series: pd.Series,
        is_high_earner: np.ndarray,
        top_k: int = 200,
    ) -> pd.DataFrame:
        """Calculates TF-IDF terms and computes differential prominence between high-earners and others."""
        logger.info("Extracting TF-IDF unigrams and bigrams...")
        stop_words = list(
            CountVectorizer(stop_words="english")
            .get_stop_words()
            .union(CUSTOM_STOPWORDS)
        )

        vectorizer = TfidfVectorizer(
            ngram_range=(1, 2),
            max_features=4000,
            min_df=15,
            max_df=0.6,
            sublinear_tf=True,
            stop_words=stop_words,
        )

        tfidf_mat = vectorizer.fit_transform(cleaned_series)
        feature_names = np.array(vectorizer.get_feature_names_out())

        # High Earner vs Non-High Earner mean TF-IDF
        high_mask = is_high_earner
        non_high_mask = ~is_high_earner

        high_tfidf_mean = np.array(tfidf_mat[high_mask].mean(axis=0)).flatten()
        non_high_tfidf_mean = np.array(tfidf_mat[non_high_mask].mean(axis=0)).flatten()

        # Overall frequency (document frequency)
        doc_freq = np.array((tfidf_mat > 0).sum(axis=0)).flatten()

        # Differential Score: ratio of high to non-high with Laplace smoothing
        eps = 1e-4
        diff_ratio = (high_tfidf_mean + eps) / (non_high_tfidf_mean + eps)
        log_diff_score = np.log(diff_ratio)
        abs_diff = high_tfidf_mean - non_high_tfidf_mean

        terms_df = pd.DataFrame(
            {
                "term": feature_names,
                "ngram_type": [
                    "unigram" if " " not in t else "bigram" for t in feature_names
                ],
                "doc_frequency": doc_freq,
                "high_earner_mean_tfidf": np.round(high_tfidf_mean, 5),
                "non_high_earner_mean_tfidf": np.round(non_high_tfidf_mean, 5),
                "diff_ratio": np.round(diff_ratio, 3),
                "log_diff_score": np.round(log_diff_score, 4),
                "abs_diff_score": np.round(abs_diff, 5),
                "is_high_earner_marker": log_diff_score > 0.2,
            }
        )

        # Sort by log_diff_score descending (top high-earner terms first)
        terms_df = terms_df.sort_values(by="log_diff_score", ascending=False)
        terms_df.to_parquet(self.config.text_terms_parquet, index=False)
        logger.info(
            f"Saved {len(terms_df)} TF-IDF terms to {self.config.text_terms_parquet}."
        )
        return terms_df

    def fit_lda_topics(
        self,
        cleaned_series: pd.Series,
        df_meta: pd.DataFrame,
        n_topics: int = 8,
    ) -> pd.DataFrame:
        """Fits LDA topic model across profiles and associates dominant topics with earnings."""
        logger.info(f"Fitting LDA topic model with K={n_topics} topics...")
        stop_words = list(
            CountVectorizer(stop_words="english")
            .get_stop_words()
            .union(CUSTOM_STOPWORDS)
        )

        count_vec = CountVectorizer(
            ngram_range=(1, 2),
            max_features=2500,
            min_df=20,
            max_df=0.5,
            stop_words=stop_words,
        )
        dtm = count_vec.fit_transform(cleaned_series)
        vocab = np.array(count_vec.get_feature_names_out())

        lda = LatentDirichletAllocation(
            n_components=n_topics,
            random_state=self.config.random_seed,
            max_iter=15,
            learning_method="online",
            batch_size=256,
            n_jobs=-1,
        )
        doc_topic_dist = lda.fit_transform(dtm)

        # Topic keyword extraction
        topic_records: list[dict[str, Any]] = []
        dominant_topics = np.argmax(doc_topic_dist, axis=1)
        df_meta["dominant_topic"] = dominant_topics

        for topic_idx, topic_weights in enumerate(lda.components_):
            top_word_indices = topic_weights.argsort()[:-16:-1]
            top_words = vocab[top_word_indices]
            top_weights = topic_weights[top_word_indices]
            top_weights_norm = top_weights / top_weights.sum()

            keywords = [
                f"{w} ({round(wt, 2)})" for w, wt in zip(top_words, top_weights_norm)
            ]

            # Metadata for users whose dominant topic is this topic
            sub_users = df_meta[df_meta["dominant_topic"] == topic_idx]
            n_users = len(sub_users)
            high_earners = int(sub_users["high_earner"].sum())
            high_rate = (high_earners / n_users) if n_users > 0 else 0.0
            med_earn = (
                float(sub_users["total_earnings"].median()) if n_users > 0 else 0.0
            )

            # Topic Title heuristic from top 3 keywords
            topic_label = f"Topic {topic_idx + 1}: {' / '.join(top_words[:3]).title()}"

            topic_records.append(
                {
                    "topic_id": topic_idx + 1,
                    "topic_label": topic_label,
                    "top_keywords": ", ".join(top_words[:10]),
                    "keywords_weighted": ", ".join(keywords),
                    "dominant_freelancer_count": n_users,
                    "high_earner_count": high_earners,
                    "high_earner_rate": round(high_rate, 4),
                    "median_earnings": round(med_earn, 2),
                    "mean_doc_weight": round(
                        float(np.mean(doc_topic_dist[:, topic_idx])), 4
                    ),
                }
            )

        topics_df = pd.DataFrame(topic_records).sort_values(
            by="high_earner_rate", ascending=False
        )
        topics_df.to_parquet(self.config.topics_parquet, index=False)
        logger.info(
            f"Saved {len(topics_df)} LDA topics to {self.config.topics_parquet}."
        )
        return topics_df

    def run(self) -> dict[str, Any]:
        self.config.ensure_directories()
        df_meta, cleaned_series, is_high_earner = self.load_corpus()
        terms_df = self.compute_differential_tfidf(cleaned_series, is_high_earner)
        topics_df = self.fit_lda_topics(
            cleaned_series, df_meta, n_topics=self.config.lda_num_topics
        )
        return {
            "total_terms": len(terms_df),
            "high_earner_marker_terms": int(terms_df["is_high_earner_marker"].sum()),
            "topics_count": len(topics_df),
        }


def run_text_analysis(config: PipelineConfig = DEFAULT_CONFIG) -> dict[str, Any]:
    analyzer = ProfileTextAnalyzer(config=config)
    return analyzer.run()


if __name__ == "__main__":
    run_text_analysis()
