import dagger
from dagger import dag, function, object_type
import base64


@object_type
class Pdfextractor:
    @function
    async def extract(self, pdf_path: dagger.Directory, page_number: int) -> str:
        """
        Extracts a specific page from a PDF and returns it as a base64 encoded string
        Args:
            pdf_path: Path to the PDF file
            page_number: Page number to extract (1-based index)
        Returns:
            Base64 encoded string of the extracted page image
        """
        # pdf_filename = pdf_path.split('/')[-1]

        return await (
            dag.container()
            .from_("python:3.9-slim")
            .with_exec(["pip", "install", "pdf2image", "Pillow"])
            .with_exec(["apt-get", "update"])
            .with_exec(["apt-get", "install", "-y", "poppler-utils"])
            .with_directory("/src", pdf_path)
            # Run the Python script to extract and encode the page
            .with_exec([
                "python", "-c",
                f"""
import base64
from pdf2image import convert_from_path
import os

# Convert specific page to image
images = convert_from_path('/src/test.pdf', first_page={page_number}, last_page={page_number})
if images:
    # Save the image temporarily
    temp_path = '/tmp/output.png'
    images[0].save(temp_path, 'PNG')
    
    # Read and encode the image
    with open(temp_path, 'rb') as img_file:
        print(base64.b64encode(img_file.read()).decode())
                """
            ])
            .stdout()
        ) 