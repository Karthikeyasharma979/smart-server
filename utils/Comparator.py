import os
import logging
import difflib

logger = logging.getLogger(__name__)

def compare_texts(text1: str, text2: str):
    """Compare two texts and provide a detailed similarity analysis using local difflib."""
    # Split texts into word sequences for more accurate word-level comparison
    words1 = text1.lower().split()
    words2 = text2.lower().split()
    
    matcher = difflib.SequenceMatcher(None, words1, words2)
    similarity_ratio = matcher.ratio() * 100
    
    # Generate a markdown report compatible with the frontend
    report = f"### System Heuristics Analysis\n\n"
    report += f"- **Estimated Overall Similarity:** {similarity_ratio:.1f}%\n"
    report += f"- **Word overlap count:** {sum(block.size for block in matcher.get_matching_blocks())} matching words found in similar sequences.\n\n"
    
    report += "#### Assessment\n"
    if similarity_ratio > 40:
        report += "- ⚠️ **High Structural Similarity Detected!** The suspect text shares a significant amount of identical phrasing, sequence structures, and vocabulary with the original source. This strongly indicates copy-pasting or minimal paraphrasing.\n"
    elif similarity_ratio > 15:
        report += "- 🔍 **Moderate Pattern Overlap.** There are overlapping word chains and concepts. This typically indicates heavily paraphrased content, summary of the same source, or use of common domain terminology.\n"
    elif similarity_ratio > 0:
        report += "- ✅ **Low Similarity Elements.** The texts appear to be largely independent. Any overlaps are likely coincidental or common conjunctions/articles.\n"
    else:
        report += "- ✨ **Complete Originality.** No measurable sequence overlap detected between the two text segments.\n"
        
    return report
