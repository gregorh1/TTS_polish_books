"""
Polish Text Preprocessor for Audiobook Production
Standalone tool to clean and prepare Polish text for TTS processing.
"""

import os
import sys
from typing import List, Optional
from pathlib import Path
import openai
from config import Config

class PolishTextPreprocessor:
    """Preprocesses Polish text for audiobook production using OpenAI."""
    
    def __init__(self):
        """Initialize the preprocessor with OpenAI configuration."""
        if not Config.validate():
            raise ValueError("OpenAI API key not configured. Please set OPENAI_API_KEY in your environment.")
        
        self.client = openai.OpenAI(api_key=Config.OPENAI_API_KEY)
        self.model = Config.OPENAI_MODEL
        
    def get_cleanup_prompt(self) -> str:
        """Get the system prompt for text cleanup."""
        return """Jesteś ekspertem od przygotowywania polskich tekstów na audiobooki. 
    Twoim zadaniem jest oczyszczenie tekstu akademickiego/historycznego tak, aby był idealny do syntezy mowy.

    ZASADY CZYSZCZENIA:

    1. **Skróty do rozwinięcia**:
       - "itd." → "i tak dalej"
       - "itp" → "i tym podobne"
       - "np." → "na przykład"
       - "tzn." → "to znaczy"
       - "m.in." → "między innymi"
       - "tj." → "to jest"
       - "tzw." → "tak zwany"
       - "przyp." → "przypis"
       - "wyd." → "wydanie"
       - "cyt." → "cytowane"
       - "s." → "strona" (gdy oznacza numer strony)
       - "dr" / "dr." → "doktor"
       - "prof." → "profesor"
       - "mgr" / "mgr." → "magister"
       - "inż." → "inżynier"
       - "mgr inż." → "magister inżynier"
       - "pt." → "pod tytułem"
       - "por." → "porównaj" (w kontekście akademickim)
       - "nt." → "na temat"

    2. **LICZBY DO TEKSTU** (BARDZO WAŻNE dla TTS):
       - Lata: "1946" → dostosuj do kontekstu gramatycznego:
         * "w 1946 roku" → "w tysiąc dziewięćset czterdziestym szóstym roku"
         * "rok 1946" → "rok tysiąc dziewięćset czterdziesty szósty"
         * "od 1946" → "od tysiąc dziewięćset czterdziestego szóstego"
       - Daty: "11 września 2001 r." → "jedenastego września dwa tysiące pierwszego roku"
       - Liczby podstawowe: "15" → "piętnaście", "301" → "trzysta jeden"
       - Procenty: "25%" → "dwadzieścia pięć procent"
       - Dziesiętne: "3.5" → "trzy i pięć dziesiątych"
       - Numeracja: "1." → "pierwszy", "2." → "drugi" (gdy to punkty listy)
       - Setki/tysiące: "2000" → "dwa tysiące"
       - Cyfry rzymskie: "XX wieku" → "dwudziestego wieku", "II RP" → "druga eR Pe", 
         "III Rzesza" → "trzecia Rzesza", "IV rozbiór" → "czwarty rozbiór"
       - Liczby porządkowe z myślnikiem: "10-ty" → "dziesiąty", "11-ty" → "jedenasty", "12-ty" → "dwunasty"
       - Listy numerowane: "Ad 1)" → "punkt pierwszy", "Ad 2)" → "punkt drugi"
       - Równania: "(1)..." → "równanie pierwsze", "(2)..." → "równanie drugie"

    3. **AKRONIMY DO FONETYKI** (WAŻNE dla TTS):
       Wszystkie akronimy przeliteruj fonetycznie po polsku:
       - "USA" → "U eS A"
       - "ZSRR" → "Zet eS eR eR"
       - "PRL" → "Pe eR eL"
       - "UE" → "U E"
       - "ONZ" → "O eN Zet"
       - "WTC" → "Wu Te Ce"
       - "IPS" → "I Pe eS"
       - "MWG" → "eM Wu Gie" 
       - "MWD" → "eM Wu De"
       - "KI" → "Ka I"
       - "GRU" → "Gie eR U"
       - "UN" → "U eN"
       - "EU" → "E U"
       - "NKWD" → "eN Ka Wu De"
       - "MGB" → "eM Gie Be"
       - "ChRL" → "Ce Ha eR eL"
       
       Wyjątki (pozostaw bez zmian):
       - "NATO" → "NATO" (powszechnie znany skrót)

    4. **FORMATOWANIE TEKSTU**:
       - Usuń niepotrzebne spacje między literami w słowach:
         * "ś w i a t o p o g l ą d u" → "światopoglądu"
         * "o g ó l n y m o d e l" → "ogólny model"
         * "p o z y c j a c z ł o w i e k a" → "pozycja człowieka"
       - Zachowaj normalne spacje między słowami.
       - Popraw błędy formatowania, takie jak "nie zamiesCzym jest nauka porównawczazczałem" → "nie zamieszczałem".
       - Inicjały w imionach: "G. W. Bush" → "Gie Wu Bush", "F. Konecznego" → "Ef Konecznego".

    5. **Usuwanie**:
       - Wszystkie numery przypisów: ¹, ², ³, 1, 2, 3 (gdy są przypisami)
       - Bibliografia i cytowania w nawiasach, np. "Por. J. Kossecki, Cybernetyka społeczna, Warszawa 1981, s. 79-80, 82-96."
       - Numerację rozdziałów/sekcji na początku linii.
       - Referencje do stron typu "(s. 301)".
       - Samodzielne numery stron wstawione w tekst (np. "92" w osobnej linii).
       - Cytowania akademickie: "Por. tamże, s. 305.", "wyd. cyt.", "Por. OBWIESZCZENIE..."
       - Puste nawiasy przerwań "(...)" w tekście.
       - Formalne tytuły dokumentów pisane WIELKIMI LITERAMI gdy przeszkadzają w narracji.

    6. **Zachowywanie**:
       - Naturalny przepływ narracji.
       - Kontekst historyczny i merytoryczny.
       - Nazwy własne osób i miejsc.
       - Znaczenie i sens treści.
       - Obcojęzyczne zwroty i tytuły w oryginale, np. "The Pacularity of Men".

    7. **Ulepszanie dla audio**:
       - Płynne przejścia między zdaniami.
       - Usuwanie zagnieżdżonych nawiasów zakłócających narrację.
       - Przekształcanie przypisów na naturalny tekst (tylko jeśli ważne merytorycznie).
       - Wszystkie liczby wymówione słowami w odpowiednim przypadku gramatycznym.
       - Akronimy przeliterowane fonetycznie dla lepszej wymowy.

    ODPOWIEDŹ: Zwróć TYLKO oczyszczony tekst, bez żadnych komentarzy czy objaśnień."""

    def chunk_text(self, text: str, max_chunk_size: int = 2500) -> List[str]:
        """
        Split text into chunks for processing.
        
        Optimized chunk size (2.5K chars) for best LLM processing reliability.
        Even though GPT-4o-mini supports 128K tokens, smaller chunks provide:
        - Better attention and focus
        - More consistent processing quality  
        - Improved reliability and error handling
        - Prevents content truncation issues
        
        Note: Chapter splitting is handled manually - this processes the full text.
        """
        if len(text) <= max_chunk_size:
            return [text]
        
        # Process full text using paragraph-based splitting
        return self._split_large_text(text, max_chunk_size)
    
    def _split_large_text(self, text: str, max_chunk_size: int) -> List[str]:
        """Split large text by paragraphs, then sentences if needed."""
        chunks = []
        
        # Try to split by paragraphs first
        paragraphs = text.split('\n\n')
        current_chunk = ""
        
        for paragraph in paragraphs:
            # Check if adding this paragraph would exceed size
            if len(current_chunk) + len(paragraph) + 2 <= max_chunk_size:
                if current_chunk:
                    current_chunk += "\n\n" + paragraph
                else:
                    current_chunk = paragraph
            else:
                # Save current chunk if it exists
                if current_chunk:
                    chunks.append(current_chunk)
                
                # Handle oversized paragraph
                if len(paragraph) > max_chunk_size:
                    # Split by sentences
                    sentences = paragraph.split('.')
                    current_chunk = ""
                    
                    for sentence in sentences:
                        if len(current_chunk) + len(sentence) + 1 <= max_chunk_size:
                            if current_chunk:
                                current_chunk += "." + sentence
                            else:
                                current_chunk = sentence
                        else:
                            if current_chunk:
                                chunks.append(current_chunk)
                            current_chunk = sentence
                else:
                    current_chunk = paragraph
        
        if current_chunk:
            chunks.append(current_chunk)
        
        return chunks

    def clean_text_chunk(self, text_chunk: str, debug: bool = False) -> str:
        """Clean a single chunk of text using OpenAI."""
        try:
            if debug:
                print(f"    🔍 DEBUG: Input chunk length: {len(text_chunk)} chars")
                print(f"    🔍 DEBUG: Input preview: {text_chunk[:100]}...")
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.get_cleanup_prompt()},
                    {"role": "user", "content": f"Oczyść ten tekst:\n\n{text_chunk}"}
                ],
                temperature=0.3,  # Lower temperature for more consistent cleaning
                max_tokens=8000  # Increased token limit to handle larger chunks
            )
            
            cleaned_text = response.choices[0].message.content.strip()
            
            if debug:
                print(f"    🔍 DEBUG: Output length: {len(cleaned_text)} chars")
                print(f"    🔍 DEBUG: Output preview: {cleaned_text[:100]}...")
            
            # Check if we got a reasonable response
            if len(cleaned_text) < 10:  # Very short response is suspicious
                print(f"    ⚠️  WARNING: Very short response ({len(cleaned_text)} chars), using original")
                return text_chunk
            
            return cleaned_text
            
        except Exception as e:
            print(f"    ❌ Error cleaning text chunk: {e}")
            return text_chunk  # Return original if cleaning fails

    def process_file(self, input_file: str, chunk_size: int = 2500, debug: bool = False) -> bool:
        """Process a single text file."""
        input_path = Path(input_file)
        
        if not input_path.exists():
            print(f"❌ File not found: {input_file}")
            return False
        
        # Create output filename with _clean suffix
        output_path = input_path.parent / f"{input_path.stem}_clean{input_path.suffix}"
        
        print(f"📖 Reading: {input_path}")
        
        try:
            with open(input_path, 'r', encoding='utf-8') as f:
                original_text = f.read()
        except Exception as e:
            print(f"❌ Error reading file: {e}")
            return False
        
        print(f"📝 Original text length: {len(original_text)} characters")
        
        # Split into chunks for processing
        chunks = self.chunk_text(original_text, chunk_size)
        print(f"🔄 Processing {len(chunks)} chunks...")
        
        cleaned_chunks = []
        for i, chunk in enumerate(chunks, 1):
            print(f"   Processing chunk {i}/{len(chunks)}...")
            if debug:
                print(f"    🔍 DEBUG: Processing chunk {i}")
            cleaned_chunk = self.clean_text_chunk(chunk, debug=debug)
            cleaned_chunks.append(cleaned_chunk)
            if debug:
                print(f"    🔍 DEBUG: Chunk {i} added to results (length: {len(cleaned_chunk)})")
                print(f"    🔍 DEBUG: Total chunks so far: {len(cleaned_chunks)}")
                print("    " + "="*50)
        
        # Combine cleaned chunks
        cleaned_text = "\n\n".join(cleaned_chunks)
        
        print(f"✨ Cleaned text length: {len(cleaned_text)} characters")
        
        # Save cleaned text
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(cleaned_text)
            print(f"✅ Saved cleaned text: {output_path}")
            return True
        except Exception as e:
            print(f"❌ Error saving file: {e}")
            return False

def estimate_cost(text_length: int, model: str = "gpt-4o-mini") -> float:
    """Estimate processing cost for the given text."""
    # Rough token estimation: 1 token ≈ 4 characters for Polish
    tokens = text_length / 4
    
    # Pricing per million tokens (input + output estimated)
    pricing = {
        "gpt-4.1-nano": {"input": 0.10, "output": 0.40},
        "gpt-4o-mini": {"input": 0.15, "output": 0.60},
        "gpt-4.1-mini": {"input": 0.40, "output": 1.60}
    }
    
    rates = pricing.get(model, pricing["gpt-4o-mini"])
    
    # Estimate output as 80% of input (cleaning usually reduces text)
    input_cost = (tokens / 1_000_000) * rates["input"]
    output_cost = (tokens * 0.8 / 1_000_000) * rates["output"]
    
    return input_cost + output_cost

def main():
    """Main function for standalone usage."""
    import argparse
    
    parser = argparse.ArgumentParser(description="🎯 Polish Text Preprocessor for Audiobooks")
    parser.add_argument("input_file", help="Input text file to process")
    parser.add_argument("--chunk-size", type=int, default=2500, 
                       help="Maximum chunk size in characters (default: 2500, optimized for reliability)")
    parser.add_argument("--estimate-cost", action="store_true",
                       help="Show cost estimate before processing")
    parser.add_argument("--model", default="gpt-4o-mini",
                       choices=["gpt-4.1-nano", "gpt-4o-mini", "gpt-4.1-mini"],
                       help="OpenAI model to use (default: gpt-4o-mini)")
    parser.add_argument("--save-chunks-only", action="store_true",
                       help="Save text chunks to file for inspection without processing them")
    parser.add_argument("--debug", action="store_true",
                       help="Enable debug output to see what OpenAI returns for each chunk")
    
    # If no arguments provided, show help
    if len(sys.argv) == 1:
        parser.print_help()
        return
    
    args = parser.parse_args()
    
    # If no path specified, assume text_sources directory
    input_file = args.input_file
    if not os.path.dirname(input_file):
        input_file = os.path.join("text_sources", input_file)
    
    # Check if file exists
    if not os.path.exists(input_file):
        print(f"❌ File not found: {input_file}")
        return
    
    # Read file to get length for cost estimation
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            text_content = f.read()
    except Exception as e:
        print(f"❌ Error reading file: {e}")
        return
    
    print(f"📖 File: {input_file}")
    print(f"📝 Text length: {len(text_content):,} characters")
    
    # Cost estimation
    estimated_cost = estimate_cost(len(text_content), args.model)
    print(f"💰 Estimated cost ({args.model}): ${estimated_cost:.4f}")
    
    if args.estimate_cost:
        print("\n💡 Cost comparison:")
        for model in ["gpt-4.1-nano", "gpt-4o-mini", "gpt-4.1-mini"]:
            cost = estimate_cost(len(text_content), model)
            print(f"   {model}: ${cost:.4f}")
        
        confirm = input("\n🔄 Proceed with processing? (y/N): ")
        if confirm.lower() != 'y':
            print("❌ Processing cancelled.")
            return
    
    # Handle save-chunks-only mode
    if args.save_chunks_only:
        print("🔍 CHUNKS ONLY MODE: Saving chunks for inspection (no processing)")
        
        # Create a temporary preprocessor instance just for chunking
        preprocessor = PolishTextPreprocessor()
        
        # Use custom chunk size if specified
        if args.chunk_size != 2500:
            print(f"🔧 Using custom chunk size: {args.chunk_size:,} characters")
        
        # Split into chunks
        chunks = preprocessor.chunk_text(text_content, args.chunk_size)
        print(f"📝 Split text into {len(chunks)} chunks")
        
        # Save chunks to file for inspection
        chunks_file = input_file.replace('.txt', '_chunks_debug.txt')
        try:
            with open(chunks_file, 'w', encoding='utf-8') as f:
                f.write(f"=== DEBUG CHUNKS FOR INSPECTION ===\n")
                f.write(f"Source file: {input_file}\n")
                f.write(f"Total chunks: {len(chunks)}\n")
                f.write(f"Chunk size setting: {args.chunk_size}\n")
                f.write(f"Original text length: {len(text_content)} characters\n\n")
                
                for i, chunk in enumerate(chunks):
                    chunk_len = len(chunk)
                    f.write(f"=== CHUNK {i+1}/{len(chunks)} ({chunk_len} characters) ===\n")
                    f.write(f"First 100 chars: {chunk[:100]}...\n")
                    f.write(f"Last 100 chars: ...{chunk[-100:]}\n")
                    f.write(f"--- FULL CHUNK CONTENT ---\n")
                    f.write(f"{chunk}\n\n")
                
                f.write(f"=== END OF CHUNKS ===\n")
            
            print(f"✅ Chunks saved to: {chunks_file}")
            print(f"📊 Summary:")
            for i, chunk in enumerate(chunks):
                chunk_len = len(chunk)
                preview = chunk[:50] + "..." if len(chunk) > 50 else chunk
                print(f"  Chunk {i+1}: {preview} ({chunk_len} chars)")
            return
            
        except Exception as e:
            print(f"❌ Error saving chunks file: {e}")
            return
    
    # Update config if different model specified
    if args.model != Config.OPENAI_MODEL:
        print(f"🔧 Using model: {args.model}")
        Config.OPENAI_MODEL = args.model
    
    # Process the file
    preprocessor = PolishTextPreprocessor()
    
    # Use custom chunk size if specified
    if args.chunk_size != 2500:
        print(f"🔧 Using custom chunk size: {args.chunk_size:,} characters")
    
    success = preprocessor.process_file(input_file, args.chunk_size, debug=args.debug)
    
    if success:
        print()
        print("🎉 Text preprocessing completed!")
        print("📁 You can now run TTS on the cleaned file.")
        print(f"💰 Actual cost: ~${estimated_cost:.4f}")
    else:
        print()
        print("❌ Text preprocessing failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()