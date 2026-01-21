from openai import OpenAI
import base64

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

def generate_image(openai_api_key="", 
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
    if system_prompt:
        prompt = f"{system_prompt}\n\n{prompt}"
    
    result = ai_client.images.generate(
        model=model or "gpt-image-1",
        prompt=prompt
    )

    image_base64 = result.data[0].b64_json
    return image_base64
