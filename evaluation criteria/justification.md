# Table: Evaluation Criteria for Generated Code Recommendations

This table shows the defined criteria for the evaluation of the generated code recommendations and why they are necessary.

| **Criterion**                         | **Importance in Code Vulnerability**                                                                                                                                                                                                                                                                   | **Justification**                                                                                                                                                                                                                                                               |
| ------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Relevance**                         | This criterion evaluates whether the recommendation aligns with the specific vulnerability and is relevant within the given context. Code vulnerabilities are context-specific, and recommendations must align with the specific vulnerability described and retrieved from the database.              | The LLM must propose solutions that directly address the identified vulnerability (CWE/CVE). This ensures the recommendation is tailored to the specific issue and effectively mitigates the security risk.                                                                     |
| **Completeness**                      | Completeness assesses whether the recommendation addresses all aspects of the vulnerability. An incomplete recommendation may only partially repair a vulnerability, leaving exploitable gaps. For example, a SQL injection repair missing input sanitization would still leave the system vulnerable. | The recommendation must cover all necessary steps to fully resolve the vulnerability, ensuring no exploitable gaps remain. Comprehensive repairs ensure that the system is fully protected against the identified security threat.                                              |
| **Correctness**                       | Correctness focuses on the technical accuracy of the recommendation. Even minor errors in the recommendation could result in ineffective repairs or introduce new vulnerabilities. Technical accuracy is critical in security, as flawed repairs can worsen the system’s security.                     | Recommendations must be factually and technically correct. Ensuring correctness avoids introducing new issues or leaving existing vulnerabilities unaddressed. Accurate and reliable repairs help developers implement secure changes effectively.                              |
| **Identification of Vulnerable Code** | Correctly identifying where the vulnerability exists in the code based on the provided context is essential. Without this, the recommendation cannot be applied effectively, and the vulnerability may remain unfixed.                                                                                 | The LLM must accurately identify the vulnerable parts of the code (e.g., specific lines or functions). This helps developers target the problem and ensures that the repair is applied in the correct location, leading to an efficient and effective vulnerability resolution. |
| **Code Guidance**                     | Providing clear code snippets that assist in implementing the repair. Security repairs must follow best practices, and actionable code examples make it easier for LLMs downstream or developers to follow through with the code repair.                                                               | The recommendation should include actionable code snippets that provide clear, practical guidance. This makes it easier for LLMs downstream to understand and implement the repair.                                                                                             |