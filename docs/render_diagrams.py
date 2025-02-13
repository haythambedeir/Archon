import os
import requests
import base64
import zlib
from PIL import Image
import io

def encode_puml(puml_content):
    """Encode PlantUML content for web URL"""
    compressed = zlib.compress(puml_content.encode('utf-8'))
    encoded = base64.b64encode(compressed)
    return encoded.decode('utf-8')

def get_diagram_url(puml_content):
    """Get PlantUML web render URL"""
    encoded = encode_puml(puml_content)
    # Try multiple PlantUML servers
    servers = [
        "https://www.plantuml.com/plantuml/png/",
        "https://plantuml.org/plantuml/png/",
        "http://plantuml.org/plantuml/png/"
    ]
    
    for server in servers:
        try:
            url = f"{server}{encoded}"
            # Test the URL first
            response = requests.head(url)
            if response.status_code == 200:
                return url
        except:
            continue
    
    raise Exception("No PlantUML server is responding")

def verify_image(image_data):
    """Verify that the image data is a valid PNG and not empty"""
    try:
        img = Image.open(io.BytesIO(image_data))
        width, height = img.size
        # Check if image is not just a blank or error image
        if width < 50 or height < 50:  # Minimum size threshold
            return False
        return True
    except:
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
    
    # Create images directory if it doesn't exist
    if not os.path.exists('docs/images'):
        os.makedirs('docs/images')
    
    success_count = 0
    failure_count = 0
    
    for dir_name in diagram_dirs:
        dir_path = f'docs/{dir_name}'
        if not os.path.exists(dir_path):
            print(f"Directory not found: {dir_path}")
            continue
            
        for file in os.listdir(dir_path):
            if file.endswith('.puml'):
                puml_path = os.path.join(dir_path, file)
                print(f"\nProcessing {puml_path}...")
                
                try:
                    with open(puml_path, 'r') as f:
                        puml_content = f.read()
                    
                    # Get diagram URL
                    url = get_diagram_url(puml_content)
                    print(f"Using URL: {url}")
                    
                    # Download PNG with retries
                    max_retries = 3
                    for attempt in range(max_retries):
                        try:
                            response = requests.get(url, timeout=30)
                            if response.status_code == 200 and verify_image(response.content):
                                png_name = file.replace('.puml', '.png')
                                png_path = os.path.join('docs/images', png_name)
                                
                                with open(png_path, 'wb') as f:
                                    f.write(response.content)
                                
                                # Verify the written file
                                if os.path.exists(png_path) and os.path.getsize(png_path) > 1000:
                                    print(f"✓ Successfully generated {png_path}")
                                    success_count += 1
                                    break
                            else:
                                print(f"Attempt {attempt + 1}: Invalid image received")
                        except Exception as e:
                            print(f"Attempt {attempt + 1} failed: {str(e)}")
                            if attempt == max_retries - 1:
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
    images_dir = 'docs/images'
    if not os.path.exists(images_dir):
        return
        
    images = [f for f in os.listdir(images_dir) if f.endswith('.png')]
    
    with open('docs/README.md', 'r') as f:
        content = f.read()
    
    # Add images section if not present
    if '## Generated Diagrams' not in content:
        content += '\n\n## Generated Diagrams\n\n'
        for image in sorted(images):
            name = image.replace('.png', '').replace('-', ' ').title()
            content += f"### {name}\n\n"
            content += f"![{name}](images/{image})\n\n"
        
        with open('docs/README.md', 'w') as f:
            f.write(content)

if __name__ == "__main__":
    print("Starting diagram generation...")
    if render_diagrams():
        update_readme_with_images()
        print("\nDiagrams have been rendered and README.md has been updated.")
    else:
        print("\nFailed to generate any valid diagrams. Please check the PlantUML syntax and server connectivity.")