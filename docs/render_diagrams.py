import os
import requests
import zlib
import base64
from pathlib import Path

def ensure_directory(path):
    """Ensure a directory exists"""
    Path(path).mkdir(parents=True, exist_ok=True)

def encode_puml(puml_content):
    """Encode PlantUML content for URL"""
    # Remove @startuml and @enduml if present
    puml_content = puml_content.replace("@startuml", "").replace("@enduml", "")
    
    # Compress using zlib
    zlibbed = zlib.compress(puml_content.encode('utf-8'))
    
    # Remove zlib header and checksum
    compressed = zlibbed[2:-4]
    
    # Encode to base64
    encoded = base64.b64encode(compressed)
    
    # Make URL-safe
    url_str = encoded.decode('ascii')
    url_str = url_str.replace('+', '-')
    url_str = url_str.replace('/', '_')
    
    return url_str

def render_diagram(puml_content, output_path):
    """Render a single PlantUML diagram"""
    try:
        # Encode the content
        encoded = encode_puml(puml_content)
        
        # Add the required tilde prefix
        encoded = "~1" + encoded
        
        # Get the PNG from PlantUML server
        url = f"http://www.plantuml.com/plantuml/png/{encoded}"
        print(f"Requesting: {url}")
        
        response = requests.get(url)
        
        if response.status_code == 200 and response.headers.get('content-type', '').startswith('image/'):
            # Save the image
            with open(output_path, 'wb') as f:
                f.write(response.content)
            return True
        else:
            print(f"Error: Server returned status {response.status_code}")
            print(f"Response content: {response.text[:200]}...")
            return False
            
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

def render_diagrams():
    """Render all PlantUML diagrams to PNG files"""
    diagram_dirs = [
        'class-diagrams',
        'sequence-diagrams',
        'activity-diagrams',
        'component-diagrams',
        'state-diagrams'
    ]
    
    # Create images directory
    ensure_directory('docs/images')
    
    success_count = 0
    failure_count = 0
    
    for dir_name in diagram_dirs:
        dir_path = os.path.join('docs', dir_name)
        if not os.path.exists(dir_path):
            print(f"Directory not found: {dir_path}")
            continue
            
        for file in os.listdir(dir_path):
            if file.endswith('.puml'):
                puml_path = os.path.join(dir_path, file)
                print(f"\nProcessing {puml_path}...")
                
                try:
                    # Read the PlantUML content
                    with open(puml_path, 'r', encoding='utf-8') as f:
                        puml_content = f.read()
                    
                    # Generate output path
                    png_name = file.replace('.puml', '.png')
                    output_path = os.path.join('docs/images', png_name)
                    
                    print(f"Rendering diagram to {output_path}...")
                    
                    if render_diagram(puml_content, output_path):
                        print(f"✓ Successfully generated {output_path}")
                        success_count += 1
                    else:
                        print(f"× Failed to generate {file}")
                        failure_count += 1
                
                except Exception as e:
                    print(f"× Error processing {file}: {str(e)}")
                    failure_count += 1
    
    print(f"\nSummary:")
    print(f"✓ Successfully generated: {success_count} diagrams")
    print(f"× Failed to generate: {failure_count} diagrams")
    
    return success_count > 0

def update_readme_with_images():
    """Update README.md with links to generated images"""
    images_dir = os.path.join('docs', 'images')
    if not os.path.exists(images_dir):
        return
        
    images = [f for f in os.listdir(images_dir) if f.endswith('.png')]
    
    with open(os.path.join('docs', 'README.md'), 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Add images section if not present
    if '## Generated Diagrams' not in content:
        content += '\n\n## Generated Diagrams\n\n'
        for image in sorted(images):
            name = image.replace('.png', '').replace('-', ' ').title()
            content += f"### {name}\n\n"
            content += f"![{name}](images/{image})\n\n"
        
        with open(os.path.join('docs', 'README.md'), 'w', encoding='utf-8') as f:
            f.write(content)

if __name__ == "__main__":
    print("Starting diagram generation...")
    if render_diagrams():
        update_readme_with_images()
        print("\nDiagrams have been rendered and README.md has been updated.")
    else:
        print("\nFailed to generate any valid diagrams. Please check the PlantUML syntax.")