from openai import OpenAI

def generate_content(openai_api_key="", 
                     openai_base_url="", model="", 
                     system_prompt="", user_prompt="", 
                     context="", question="", additional_command=""):
    ai_client = OpenAI(api_key=openai_api_key, base_url=openai_base_url)
    # Replace known placeholders without interpreting other braces.
    prompt = (
        user_prompt
        .replace("{context}", str(context))
        .replace("{question}", str(question))
        .replace("{additional_command}", str(additional_command))
    )
    print(prompt)
    response = ai_client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ]
    )
    answer = response.choices[0].message.content
    return answer
