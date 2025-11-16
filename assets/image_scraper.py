#!/usr/bin/env python3
"""
Image Scraper Script
Downloads and saves weather images from various sources for use in blog posts.
"""

import argparse
import logging
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

import requests

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# CW3E West-WRF constants
BASE_URL = "https://cw3e.ucsd.edu/images/wwrf/images/ensemble/"
SITES: Dict[str, str] = {
    "paradis": "West-WRF_3hrSnow_Meteogram_Panel_MRNP.png",
    "stevens": "West-WRF_3hrSnow_Meteogram_Panel_STP.png",
    "crystal": "West-WRF_3hrSnow_Meteogram_Panel_CMP.png",
    "snoqualmie": "West-WRF_3hrSnow_Meteogram_Panel_SNQ.png",
    "baker": "West-WRF_3hrSnow_Meteogram_Panel_MTB.png",
    "white": "West-WRF_3hrSnow_Meteogram_Panel_WHP.png",
}


def _download_file(
    url: str,
    dest_path: Path,
    session: Optional[requests.Session] = None,
    timeout: int = 10,
    retries: int = 3
) -> None:
    """
    Download a file from a URL with retry logic.
    
    Args:
        url: URL to download from
        dest_path: Destination path to save file
        session: Optional requests session to use
        timeout: Request timeout in seconds
        retries: Number of retry attempts
    
    Raises:
        requests.RequestException: If download fails after all retries
        ValueError: If response is not a valid image
    """
    if session is None:
        session = requests.Session()
    
    last_exception = None
    for attempt in range(retries):
        try:
            logger.debug(f"Downloading {url} (attempt {attempt + 1}/{retries})")
            response = session.get(url, timeout=timeout)
            
            # Validate response
            if response.status_code != 200:
                raise requests.RequestException(
                    f"HTTP {response.status_code}: Failed to download from {url}"
                )
            
            content_type = response.headers.get('Content-Type', '')
            if not content_type.startswith('image/'):
                raise ValueError(
                    f"Invalid content type '{content_type}' for URL {url}, expected image/*"
                )
            
            # Save the file
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            dest_path.write_bytes(response.content)
            
            # Set file permissions
            os.chmod(dest_path, 0o644)
            
            logger.info(f"Successfully downloaded {url} to {dest_path}")
            return
            
        except (requests.RequestException, ValueError) as e:
            last_exception = e
            logger.warning(f"Attempt {attempt + 1} failed: {e}")
            if attempt < retries - 1:
                # Exponential backoff
                sleep_time = 2 ** attempt
                logger.debug(f"Retrying in {sleep_time} seconds...")
                time.sleep(sleep_time)
    
    # All retries failed
    raise last_exception


def download_cw3e_westwrf_snow(
    sites: Optional[Dict[str, str]] = None,
    target_root: os.PathLike = Path("assets/images/cw3e")
) -> Dict[str, Path]:
    """
    Download CW3E West-WRF 3hr snow meteogram panel images.
    
    Downloads images for specified sites (or all sites if not specified),
    saving both a canonical filename and a timestamped archival copy.
    
    Args:
        sites: Optional dict mapping site names to source filenames.
               If None, uses the SITES constant.
        target_root: Root directory for saving images (default: assets/images/cw3e/)
    
    Returns:
        Dict mapping site name to the canonical saved file path
    
    Raises:
        Exception: If any download fails, describing which site failed
    """
    if sites is None:
        sites = SITES
    
    target_root = Path(target_root)
    logger.info(f"Starting CW3E West-WRF snow image download for {len(sites)} sites")
    logger.info(f"Target root directory: {target_root}")
    
    results: Dict[str, Path] = {}
    session = requests.Session()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    try:
        for site, filename in sites.items():
            logger.info(f"Processing site: {site}")
            
            # Construct URL
            url = BASE_URL + filename
            
            # Create site directory
            site_dir = target_root / site
            site_dir.mkdir(parents=True, exist_ok=True)
            os.chmod(site_dir, 0o755)
            
            # Define paths for canonical and archival copies
            canonical_path = site_dir / filename
            
            # Extract base name and extension for timestamped copy
            base_name = filename.rsplit('.', 1)[0]
            extension = filename.rsplit('.', 1)[1] if '.' in filename else 'png'
            timestamped_filename = f"{base_name}_{timestamp}.{extension}"
            timestamped_path = site_dir / timestamped_filename
            
            try:
                # Download to canonical location
                _download_file(url, canonical_path, session=session)
                
                # Copy to timestamped archive
                timestamped_path.write_bytes(canonical_path.read_bytes())
                os.chmod(timestamped_path, 0o644)
                logger.info(f"Archived copy saved to {timestamped_path}")
                
                results[site] = canonical_path
                
            except Exception as e:
                error_msg = f"Failed to download image for site '{site}' from {url}: {e}"
                logger.error(error_msg)
                raise Exception(error_msg) from e
    
    finally:
        session.close()
    
    logger.info(f"Successfully downloaded images for {len(results)} sites")
    return results


def main():
    """Main entry point for CLI execution."""
    parser = argparse.ArgumentParser(
        description='Download weather images from various sources',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '--cw3e-westwrf-snow',
        action='store_true',
        help='Download CW3E West-WRF 3hr snow meteogram panels'
    )
    
    parser.add_argument(
        '--sites',
        type=str,
        help='Comma-separated list of sites to download (subset of available sites)'
    )
    
    parser.add_argument(
        '--target-root',
        type=str,
        help='Override default target root directory for downloads'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose/debug logging'
    )
    
    args = parser.parse_args()
    
    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Handle CW3E West-WRF snow download
    if args.cw3e_westwrf_snow:
        logger.info("Starting CW3E West-WRF snow image download")
        
        # Parse sites if provided
        sites_dict = None
        if args.sites:
            site_names = [s.strip() for s in args.sites.split(',')]
            sites_dict = {name: SITES[name] for name in site_names if name in SITES}
            
            # Warn about invalid site names
            invalid_sites = [name for name in site_names if name not in SITES]
            if invalid_sites:
                logger.warning(f"Invalid site names ignored: {invalid_sites}")
                logger.info(f"Valid sites are: {list(SITES.keys())}")
            
            if not sites_dict:
                logger.error("No valid sites specified")
                return 1
        
        # Parse target root if provided
        target_root = args.target_root if args.target_root else "assets/images/cw3e"
        
        try:
            results = download_cw3e_westwrf_snow(sites=sites_dict, target_root=target_root)
            
            print("\n" + "=" * 60)
            print("Download Results:")
            print("=" * 60)
            for site, path in results.items():
                print(f"  {site:15} -> {path}")
            print("=" * 60)
            print(f"\nSuccessfully downloaded {len(results)} images")
            
            return 0
            
        except Exception as e:
            logger.error(f"Download failed: {e}")
            return 1
    
    else:
        parser.print_help()
        return 0


if __name__ == '__main__':
    exit(main())
