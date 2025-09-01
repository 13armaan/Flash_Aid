import sys

async def prompt(q:str,rows:list)->str:
    cites=[]
    ctx=[]
    for i,(text,title,url,src) in enumerate(rows,start=1):
        cites.append(f"[{i}] {title} - {url}")
        ctx.append(f"(Source {i}: {src}) {text[:1000]}")
    instructions=(
        """
        You are a cautious health assistant. Answer clearly in bullet points
        Cite sources inline like[1], [2]. Add first-aid steps when relevant
        Explicity say this is not medical advice
        """
    )
    return instructions +"\n\nContext:\n" + "\n\n".join(ctx) + f"\n\nQuestions:{q}\n"

if __name__ == "__main__":
    
#This is now both executable from cli and can also be imported
    query = sys.argv[1] if len(sys.argv) > 1 else "What to do for burns?"
    fake_rows = [
        {"text": "Cool the burn under running water.", "title": "First Aid Burn", "url": "http://example.com/burn", "source": "WHO"},
        {"text": "Do not apply butter.", "title": "Medical Burn Advice", "url": "http://example.com/burn2", "source": "CDC"}
    ]
    prompt = prompt(query, fake_rows)
    print(prompt)