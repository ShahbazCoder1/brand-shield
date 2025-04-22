import numpy as np
import re
import string
from collections import Counter
import math
# Removed image processing libraries: requests, PIL, io, imagehash
import statistics

class AIContentDetector:
    def __init__(self):
        # Common English word frequencies for comparison
        self.common_words = self._load_common_words()
        # Common AI text patterns - Expanded list for potentially newer patterns
        self.ai_patterns = [
            r"as (an|a) (AI|artificial intelligence|language model)",
            r"I (cannot|can't) (provide|access|browse|view)",
            r"(based on|according to) (my training|my knowledge|the information provided)",
            r"it's important to note that",
            r"it is worth mentioning that",
            r"there are several (factors|aspects|elements) to consider",
            r"in conclusion", # Often used to structure AI responses
            r"ultimately", # Another common concluding word
            r"however, it is important to note", # Common transition
            r"on the one hand.+on the other hand", # Balanced phrasing
            r"in summary", # Summarization phrase
            r"it is crucial to understand that", # Emphatic phrasing
            r"this highlights the importance of", # Connective phrase
            r"facilitate", "optimize", "implement", "leverage", # Common AI-favored vocabulary
            r"(in order to|so as to)", # Formal phrasing
            r"delve into", # Formal phrasing
            r"explore the nuances of" # Formal phrasing
        ]

    def _load_common_words(self):
        """Load frequency distribution of common English words"""
        # This would ideally load from a file, but for simplicity we'll use a small dict
        return {
            "the": 0.07, "of": 0.036, "and": 0.034, "to": 0.028, "a": 0.022,
            "in": 0.021, "is": 0.015, "that": 0.011, "for": 0.009, "it": 0.008,
            "as": 0.008, "with": 0.007, "was": 0.007, "on": 0.006, "be": 0.006
        }

    def detect_ai_text(self, text):
        """
        Analyze text to determine likelihood of being AI-generated
        Returns a score from 0-1 (higher = more likely AI-generated)
        """
        if not text or len(text) < 20:
            return 0.5  # Not enough text to analyze

        # Normalize text
        text = text.lower()

        # Calculate various metrics
        scores = {
            "perplexity": self._calculate_perplexity(text),
            "burstiness": self._calculate_burstiness(text),
            "repetition": self._detect_repetitive_patterns(text),
            "ai_patterns": self._detect_ai_patterns(text),
            "sentence_variety": self._analyze_sentence_variety(text),
            "word_frequency": self._analyze_word_frequency(text)
        }

        # Combine scores with weights - Slightly adjusted weights
        weights = {
            "perplexity": 0.20, # Slightly reduced weight
            "burstiness": 0.15, # Slightly reduced weight
            "repetition": 0.15,
            "ai_patterns": 0.30, # Increased weight for patterns
            "sentence_variety": 0.10,
            "word_frequency": 0.10
        }

        final_score = sum(scores[k] * weights[k] for k in scores)

        # Return normalized score
        return min(max(final_score, 0.0), 1.0)

    def _calculate_perplexity(self, text):
        """
        Calculate perplexity - a measure of how predictable the text is
        AI tends to have lower perplexity (more predictable)
        """
        words = self._tokenize(text)
        if len(words) < 5:
            return 0.5

        # Create a basic language model using n-grams
        bigrams = Counter(zip(words, words[1:]))
        unigrams = Counter(words)

        # Calculate a simple proxy for perplexity
        total_log_prob = 0
        for i in range(1, len(words)):
            bigram = (words[i-1], words[i])
            # Add smoothing
            prob = (bigrams[bigram] + 0.01) / (unigrams[words[i-1]] + 0.01 * len(unigrams))
            total_log_prob += math.log(prob) if prob > 0 else -10

        avg_log_prob = total_log_prob / (len(words) - 1) if len(words) > 1 else -10
        perplexity = math.exp(-avg_log_prob)

        # Normalize perplexity to a 0-1 score
        # Lower perplexity (more predictable) = higher AI score
        # Adjusted normalization range slightly
        return 1 - min(1, max(0, (perplexity - 5) / 150))


    def _calculate_burstiness(self, text):
        """
        Calculate burstiness - human writing tends to be more bursty than AI
        """
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]

        if len(sentences) < 3:
            return 0.5

        # Calculate sentence length variance
        sent_lengths = [len(self._tokenize(s)) for s in sentences]

        if not sent_lengths:
            return 0.5

        try:
            variance = statistics.variance(sent_lengths) if len(sent_lengths) > 1 else 0
            mean_length = statistics.mean(sent_lengths)

            # Calculate coefficient of variation
            cv = math.sqrt(variance) / mean_length if mean_length > 0 else 0

            # AI text tends to have less variation
            # Lower cv = higher AI score
            # Adjusted normalization range slightly
            return 1 - min(1, max(0, cv / 0.7)) # Increased divisor to make lower CV less indicative of AI


        except: # Catch potential errors with statistics calculation on small inputs
            return 0.5

    def _detect_repetitive_patterns(self, text):
        """
        Detect repetitive phrases and structures
        """
        # Look for repeated n-grams
        words = self._tokenize(text)
        if len(words) < 5:
            return 0.5

        # Check for trigram repetition
        trigrams = Counter([' '.join(words[i:i+3]) for i in range(len(words)-2)])
        most_common = trigrams.most_common(1)

        if most_common and most_common[0][1] > 2:
            # Repeated phrases detected - Increased score for repetition
            return 0.8 + min(0.2, most_common[0][1] / 15)


        # Check for structural repetition (similar sentence beginnings)
        sentence_starters = [s.split()[:2] for s in re.split(r'[.!?]+', text) if s.strip() and len(s.split()) > 2]
        starter_counts = Counter([' '.join(starter) for starter in sentence_starters])

        if starter_counts and starter_counts.most_common(1)[0][1] > len(sentence_starters) / 4: # Slightly relaxed threshold
            return 0.7

        return 0.2  # Default - low repetition suggests more human-like


    def _detect_ai_patterns(self, text):
        """
        Look for linguistic patterns common in AI-generated text
        """
        pattern_matches = 0
        for pattern in self.ai_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                pattern_matches += 1

        if pattern_matches > 0:
            # Increased impact of pattern matches
            return min(1.0, 0.4 + pattern_matches * 0.15)


        # Check for hedging language - Slightly increased impact
        hedging_words = ["may", "might", "could", "possibly", "perhaps", "appears to", "seems to"]
        hedging_count = sum(1 for word in hedging_words if " " + word + " " in " " + text.lower() + " ")

        if hedging_count > 2:
            return 0.7 + min(0.2, hedging_count * 0.07)


        return 0.2  # Default - low evidence of AI patterns


    def _analyze_sentence_variety(self, text):
        """
        Analyze sentence structure variety
        AI often uses more uniform sentence structures
        """
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]

        if len(sentences) < 3:
            return 0.5

        # Calculate average and std deviation for sentence lengths
        sent_lengths = [len(s) for s in sentences]
        mean_length = sum(sent_lengths) / len(sent_lengths) if sent_lengths else 0
        std_dev = math.sqrt(sum((l - mean_length) ** 2 for l in sent_lengths) / len(sent_lengths)) if sent_lengths else 0


        # Calculate coefficient of variation
        cv = std_dev / mean_length if mean_length > 0 else 0

        # More uniform sentence lengths = higher AI score
        # Adjusted normalization range slightly
        return 1 - min(1, max(0, cv / 0.6)) # Increased divisor


    def _analyze_word_frequency(self, text):
        """
        Compare word frequencies to typical human writing
        """
        words = self._tokenize(text)
        word_freq = Counter(words)
        total_words = len(words)

        if total_words < 10:
            return 0.5

        # Compare the distribution of common words with expected frequencies
        common_diff = 0
        common_count = 0

        for word, expected_freq in self.common_words.items():
            if word in word_freq:
                actual_freq = word_freq[word] / total_words
                common_diff += abs(actual_freq - expected_freq)
                common_count += 1

        if common_count == 0:
            return 0.5

        avg_diff = common_diff / common_count

        # Large differences may indicate AI text
        # Adjusted scaling
        return min(1, max(0, avg_diff * 25)) # Increased multiplier


    def _tokenize(self, text):
        """Simple tokenization for our purposes"""
        # Remove punctuation and split by whitespace
        text = text.lower()
        text = text.translate(str.maketrans('', '', string.punctuation))
        return text.split()

    # Removed image detection methods: detect_ai_image, _check_symmetry, _analyze_noise, _detect_artifacts


def detect_ecommerce_product(product_info):
    """
    Analyze a product listing for signs of AI generation (text only)

    Args:
        product_info: Dictionary with product details
            - title: Product title
            - description: Product description
            # Removed image_urls from consideration

    Returns:
        Dictionary with AI detection scores for text components
    """
    detector = AIContentDetector()

    results = {
        "overall_score": 0,
        "components": {}
    }

    # Analyze title
    if "title" in product_info and product_info["title"]:
        title_score = detector.detect_ai_text(product_info["title"])
        results["components"]["title"] = {
            "score": title_score,
            "interpretation": interpret_score(title_score)
        }

    # Analyze description
    if "description" in product_info and product_info["description"]:
        desc_score = detector.detect_ai_text(product_info["description"])
        results["components"]["description"] = {
            "score": desc_score,
            "interpretation": interpret_score(desc_score)
        }

    # Removed image analysis part

    # Calculate overall score (weighted average)
    # Weights are adjusted as image analysis is removed
    weights = {
        "title": 0.40, # Increased weight for title
        "description": 0.60, # Increased weight for description
    }

    component_scores = {}
    if "title" in product_info and product_info["title"]:
        component_scores["title"] = results["components"]["title"]["score"]
    if "description" in product_info and product_info["description"]:
        component_scores["description"] = results["components"]["description"]["score"]
    # Removed image_avg from component_scores


    if component_scores:
        # Calculate weighted score using available components
        available_weights = {k: weights[k] for k in component_scores.keys() if k in weights}
        weight_sum = sum(available_weights.values())

        if weight_sum > 0:
            overall_score = sum(component_scores[k] * available_weights[k] for k in available_weights) / weight_sum
            results["overall_score"] = overall_score
            results["overall_interpretation"] = interpret_score(overall_score)

    return results

def interpret_score(score):
    """Interpret AI detection score"""
    if score < 0.3:
        return "Likely human-created"
    elif score < 0.5:
        return "Probably human with some AI elements"
    elif score < 0.7:
        return "Possibly AI-generated"
    elif score < 0.9:
        return "Likely AI-generated"
    else:
        return "Almost certainly AI-generated"

# Example usage
if __name__ == "__main__":
    # Example product from a crawler (image_urls is ignored now)
    product = {
        "title": "SonicPulse Pro Wireless Over-Ear Headphones with ANC & 60H Battery – Bluetooth 5.3, Deep Bass, Foldable Design, Mic for Calls & Gaming – Black",
        "description": """Immerse Yourself in Pure Sound with SonicPulse Pro

Upgrade your audio experience with the SonicPulse Pro Wireless Over-Ear Headphones – engineered for music lovers, gamers, and professionals alike. These premium headphones combine cutting-edge technology with comfort and style to deliver high-fidelity sound, crystal-clear calls, and uninterrupted entertainment.""",
        "image_urls": ["https://example.com/tv1.jpg", "https://example.com/tv2.jpg"] # This list is now ignored
    }

    results = detect_ecommerce_product(product)
    print(f"Overall AI Detection Score: {results['overall_score']:.2f} - {results['overall_interpretation']}")
    print("\nComponent Analysis:")
    for component, data in results["components"].items():
        if "score" in data:
            print(f"- {component}: {data['score']:.2f} - {data['interpretation']}")
