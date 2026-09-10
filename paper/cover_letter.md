Dear Editor,

I am pleased to submit our manuscript, "The Notebook You Read Is Not the Notebook That Ran: Execution-Order Reconstruction for LLM Understanding of Jupyter Notebooks," for consideration as a Research Paper in Empirical Software Engineering.

This manuscript studies a specific, underexamined mismatch between how Jupyter notebook files are stored and how large language models (LLMs) are increasingly asked to read and reason about them: a `.ipynb` file records cells in the visual order a user left them in, which routinely diverges from the true execution order, and its raw JSON format buries most of its content behind base64 images, redundant MIME bundles, and metadata. We present JupPreprocessor, a deterministic, zero-LLM-cost serializer built around an explicit three-tier framework that separates what can be statically resolved, what can only be detected and flagged because the information is genuinely absent from the file, and what would require live code execution to know for certain.

We believe this work is a good fit for Empirical Software Engineering because its central contribution is empirical rather than purely architectural: we evaluate the approach on a fair, context-bounded synthetic benchmark spanning fifteen large language models across seven vendors, and separately on executable ground truth obtained by actually re-executing 112 real, previously crashed machine-learning notebooks under both their visual and true execution orders. We report both results in full, including a null result: on the real-notebook evaluation, our serializer shows no measurable per-item accuracy advantage over a plain compression baseline once a model answers, a finding that survived, rather than reversed, an internal audit that found and corrected a bug in our own automated grading process. The paper documents this correction process, along with a separate verified edge case in our own core reordering mechanism and a corrected explanation for a negative result on an existing benchmark, in full rather than omitting them. We consider this level of methodological transparency, including reporting where our method does not show an advantage, to be consistent with the standards of empirical software engineering research and directly relevant to researchers and practitioners currently building LLM-based tools for code and notebook understanding.

This manuscript is original, has not been published previously, and is not currently under consideration at any other journal. All authors have approved the submission. The complete source code, all measured reports underlying the manuscript's quantitative claims, and the full project history are available at a public GitHub repository, cited in the manuscript's Data Availability statement.

Per the journal's authorship policy, we disclose that large language models and an LLM-based coding/research agent were used during this project, both as the subject of evaluation and as research and drafting assistance; the exact scope of this use is documented explicitly in the manuscript's Methods section, and the corresponding author takes full responsibility for the accuracy of every claim made.

Thank you for considering our manuscript. I look forward to your response.

Sincerely,

MD. Raiyan Bin Rafique
Department of Computer Science and Engineering
Rajshahi University of Engineering and Technology, Rajshahi, Bangladesh
raiyanrohit10@gmail.com
