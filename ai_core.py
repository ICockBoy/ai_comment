import nltk

from nltk.tokenize import sent_tokenize
from nltk.corpus import stopwords
from heapq import nlargest

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

import emoji

from langdetect import detect
import dbm

import random

nltk.download('punkt')
nltk.download('stopwords')


class CommentGenerator:

    def __init__(self):

        self.cache = dbm.open('ai_cache/cache', 'c')

    def is_post_text_equal(self, post_text: str, answer: str) -> bool:
        return True if post_text == answer else False

    def calculate_similarity(self, text1: str, text2: str) -> int:

        vectorizer = TfidfVectorizer()

        tfidf_matrix = vectorizer.fit_transform([text1, text2])

        similarity_score = cosine_similarity(tfidf_matrix[0], tfidf_matrix[1])[0][0]
        similarity_percentage = round(similarity_score * 100, 2)

        return similarity_percentage

    def has_emoji(self, text: str) -> bool:

        for character in text:
            if emoji.is_emoji(character):
                return True

        return False

    def _cache_write_key(self, key: str):

        if not self.cache.get(key):
            self.cache[key] = 'exists'

    def _cache_is_key_exists(self, key: str) -> bool:
        return True if self.cache.get(key) else False

    def summarize_text(self, text: str, num_sentences: int) -> str:

        sentences = sent_tokenize(text, 'russian')

        stop_words = set(stopwords.words('russian'))
        words = nltk.word_tokenize(text, 'russian')
        words = [word for word in words if word.lower() not in stop_words]

        word_frequencies = {}
        for word in words:
            if word not in word_frequencies:
                word_frequencies[word] = 1
            else:
                word_frequencies[word] += 1

        maximum_frequency = max(word_frequencies.values())
        for word in word_frequencies:
            word_frequencies[word] = (word_frequencies[word] / maximum_frequency)

        sentence_scores = {}
        for sent in sentences:
            for word in nltk.word_tokenize(sent.lower(), 'russian'):
                if word in word_frequencies:
                    if len(sent.split(' ')) < 30:
                        if sent not in sentence_scores:
                            sentence_scores[sent] = word_frequencies[word]
                        else:
                            sentence_scores[sent] += word_frequencies[word]

        summary_sentences = nlargest(num_sentences, sentence_scores, key=sentence_scores.get)
        summary = ' '.join(summary_sentences)

        return summary

    async def generate_comment(self, post_text: str, token: str = None) -> str | None | bool:

        post_text = self.summarize_text(post_text, 1) if len(post_text) > 1000 else post_text
        import openai_async
        try:
            response = await openai_async.complete(
                api_key=token,
                timeout=20,
                payload={
                    "model": "text-davinci-001",
                    "prompt": f'Напиши комментарий на русском с добавлением емоджи на русском языке с похвалой и благодарностью на пост «{post_text}»',
                    "max_tokens": 512,
                    "n": 1,
                    "stop": None
                },
            )
        except:
            return False
        response = response.json()
        if "error" in response:
            if response["error"]["type"] == "insufficient_quota" or response['error']['code'] == 'invalid_api_key':
                return None
            else:
                return False
        answer = response['choices'][0]['text'].strip()

        # good_filters = [
        #     detect(answer) == 'ru',
        #     not self._cache_is_key_exists(answer),
        #     'пост' not in answer.lower(),
        #     'коммент' not in answer.lower(),
        #     'реакц' not in answer.lower(),
        #     not self.is_post_text_equal(post_text, answer),
        #     self.calculate_similarity(post_text, answer) < 40,
        #     # self.has_emoji(answer)
        # ]

        # if all(good_filters):
        #     self._cache_write_key(answer)
        #     return answer
        return answer
