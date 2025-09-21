"""
Image Resizer Tool
Python Developer Internship - Task 7
Objective: Resize and convert images in batch
Tools: Python, Pillow (PIL)
"""

import os
import sys
from PIL import Image
import argparse
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ImageResizer:
    """
    A class to handle batch image resizing and format conversion
    """
    
    SUPPORTED_FORMATS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp'}
    
    def __init__(self, input_folder, output_folder=None, target_size=None, 
                 maintain_aspect_ratio=True, output_format=None, quality=85):
        """
        Initialize the Image Resizer
        
        Args:
            input_folder (str): Path to folder containing images
            output_folder (str): Path to output folder (default: creates 'resized' subfolder)
            target_size (tuple): Target size as (width, height) in pixels
            maintain_aspect_ratio (bool): Whether to maintain aspect ratio
            output_format (str): Output format (jpg, png, etc.)
            quality (int): JPEG quality (1-100, default 85)
        """
        self.input_folder = Path(input_folder)
        self.output_folder = Path(output_folder) if output_folder else self.input_folder / 'resized'
        self.target_size = target_size or (800, 600)
        self.maintain_aspect_ratio = maintain_aspect_ratio
        self.output_format = output_format.lower() if output_format else None
        self.quality = quality
        
        # Statistics
        self.processed = 0
        self.failed = 0
        self.skipped = 0
        
    def create_output_folder(self):
        """Create output folder if it doesn't exist"""
        self.output_folder.mkdir(parents=True, exist_ok=True)
        logger.info(f"Output folder ready: {self.output_folder}")
        
    def get_image_files(self):
        """Get all supported image files from input folder"""
        image_files = []
        
        for file_path in self.input_folder.iterdir():
            if file_path.is_file() and file_path.suffix.lower() in self.SUPPORTED_FORMATS:
                image_files.append(file_path)
                
        logger.info(f"Found {len(image_files)} image(s) to process")
        return image_files
    
    def calculate_new_size(self, original_size):
        """
        Calculate new size based on target size and aspect ratio preference
        
        Args:
            original_size (tuple): Original image size (width, height)
            
        Returns:
            tuple: New size (width, height)
        """
        if not self.maintain_aspect_ratio:
            return self.target_size
        
        orig_width, orig_height = original_size
        target_width, target_height = self.target_size
        
        # Calculate aspect ratios
        orig_ratio = orig_width / orig_height
        
        # Calculate new dimensions maintaining aspect ratio
        if orig_width > orig_height:
            new_width = target_width
            new_height = int(target_width / orig_ratio)
        else:
            new_height = target_height
            new_width = int(target_height * orig_ratio)
            
        # Ensure dimensions don't exceed target
        if new_height > target_height:
            new_height = target_height
            new_width = int(target_height * orig_ratio)
        if new_width > target_width:
            new_width = target_width
            new_height = int(target_width / orig_ratio)
            
        return (new_width, new_height)
    
    def resize_image(self, image_path):
        """
        Resize a single image
        
        Args:
            image_path (Path): Path to the image file
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Open the image
            with Image.open(image_path) as img:
                logger.info(f"Processing: {image_path.name} ({img.size[0]}x{img.size[1]})")
                
                # Convert RGBA to RGB if needed for JPEG output
                if self.output_format in ['jpg', 'jpeg'] and img.mode in ['RGBA', 'LA', 'P']:
                    # Create a white background
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'P':
                        img = img.convert('RGBA')
                    background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                    img = background
                
                # Calculate new size
                new_size = self.calculate_new_size(img.size)
                
                # Resize the image using high-quality Lanczos resampling
                resized_img = img.resize(new_size, Image.Resampling.LANCZOS)
                
                # Determine output filename and format
                output_format = self.output_format or image_path.suffix[1:].lower()
                output_filename = image_path.stem + '.' + output_format
                output_path = self.output_folder / output_filename
                
                # Save the resized image
                save_kwargs = {'format': output_format.upper()}
                if output_format in ['jpg', 'jpeg']:
                    save_kwargs['quality'] = self.quality
                    save_kwargs['optimize'] = True
                
                resized_img.save(output_path, **save_kwargs)
                
                # Log the result
                original_size = os.path.getsize(image_path) / 1024  # KB
                new_file_size = os.path.getsize(output_path) / 1024  # KB
                
                logger.info(f"  ✓ Resized to {new_size[0]}x{new_size[1]}")
                logger.info(f"  ✓ Size: {original_size:.1f}KB → {new_file_size:.1f}KB")
                logger.info(f"  ✓ Saved as: {output_path.name}")
                
                self.processed += 1
                return True
                
        except Exception as e:
            logger.error(f"  ✗ Failed to process {image_path.name}: {str(e)}")
            self.failed += 1
            return False
    
    def process_batch(self):
        """Process all images in the input folder"""
        logger.info("=" * 50)
        logger.info("Starting batch image resize process")
        logger.info(f"Input folder: {self.input_folder}")
        logger.info(f"Target size: {self.target_size[0]}x{self.target_size[1]}")
        logger.info(f"Maintain aspect ratio: {self.maintain_aspect_ratio}")
        if self.output_format:
            logger.info(f"Output format: {self.output_format}")
        logger.info("=" * 50)
        
        # Create output folder
        self.create_output_folder()
        
        # Get all image files
        image_files = self.get_image_files()
        
        if not image_files:
            logger.warning("No supported image files found in the input folder")
            return
        
        # Process each image
        for i, image_path in enumerate(image_files, 1):
            logger.info(f"\n[{i}/{len(image_files)}] Processing image...")
            self.resize_image(image_path)
        
        # Print summary
        self.print_summary()
    
    def print_summary(self):
        """Print processing summary"""
        logger.info("\n" + "=" * 50)
        logger.info("PROCESSING COMPLETE")
        logger.info("=" * 50)
        logger.info(f"✓ Successfully processed: {self.processed} images")
        if self.failed > 0:
            logger.info(f"✗ Failed to process: {self.failed} images")
        if self.skipped > 0:
            logger.info(f"⊘ Skipped: {self.skipped} images")
        logger.info(f"Output folder: {self.output_folder}")


def main():
    """Main function with command-line interface"""
    parser = argparse.ArgumentParser(
        description='Batch Image Resizer Tool - Resize and convert images in bulk',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python image_resizer.py /path/to/images --size 1024 768
  python image_resizer.py /path/to/images --size 500 500 --format jpg
  python image_resizer.py /path/to/images --size 800 600 --no-aspect-ratio
  python image_resizer.py /path/to/images --output /path/to/output --quality 90
        """
    )
    
    parser.add_argument(
        'input_folder',
        help='Path to folder containing images to resize'
    )
    
    parser.add_argument(
        '--output', '-o',
        dest='output_folder',
        help='Output folder path (default: creates "resized" subfolder in input folder)'
    )
    
    parser.add_argument(
        '--size', '-s',
        nargs=2,
        type=int,
        default=[800, 600],
        metavar=('WIDTH', 'HEIGHT'),
        help='Target size in pixels (default: 800 600)'
    )
    
    parser.add_argument(
        '--format', '-f',
        dest='output_format',
        choices=['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp'],
        help='Convert images to specified format'
    )
    
    parser.add_argument(
        '--quality', '-q',
        type=int,
        default=85,
        choices=range(1, 101),
        metavar='[1-100]',
        help='JPEG quality (1-100, default: 85)'
    )
    
    parser.add_argument(
        '--no-aspect-ratio',
        action='store_false',
        dest='maintain_aspect_ratio',
        help='Do not maintain aspect ratio (may distort images)'
    )
    
    args = parser.parse_args()
    
    # Validate input folder
    if not os.path.exists(args.input_folder):
        logger.error(f"Error: Input folder '{args.input_folder}' does not exist")
        sys.exit(1)
    
    if not os.path.isdir(args.input_folder):
        logger.error(f"Error: '{args.input_folder}' is not a directory")
        sys.exit(1)
    
    # Create resizer instance
    resizer = ImageResizer(
        input_folder=args.input_folder,
        output_folder=args.output_folder,
        target_size=tuple(args.size),
        maintain_aspect_ratio=args.maintain_aspect_ratio,
        output_format=args.output_format,
        quality=args.quality
    )
    
    # Process images
    try:
        resizer.process_batch()
    except KeyboardInterrupt:
        logger.info("\n\nProcess interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"An unexpected error occurred: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
