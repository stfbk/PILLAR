from openai import OpenAI
client = OpenAI(api_key="sk-proj-N3pD2I0njZxT5pfmgTMhT3BlbkFJkbgCEio1ScUC90cRGNjA")

primaryColor="#f3b61f"
backgroundColor="#38433f"
secondaryBackgroundColor="#485b55"

response = client.images.generate(
  model="dall-e-3",
  prompt="The logo of a cyber privacy company. The logo should be simple and modern. The primary color has to be #f3b61f, and the background color has to be #485b55.",
  size="1024x1024",
  quality="standard",
  n=1,
)

image_url = response.data[0].url
print(image_url)
print(response.data[0].revised_prompt)