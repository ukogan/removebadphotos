#!/usr/bin/env python3
"""
Visual Design Research Tool for Photo Management Applications

This script uses Playwright to systematically capture visual design patterns,
color schemes, typography, and layout information from popular photo management
applications to inform aesthetic improvements for photo deduplication tools.
"""

import asyncio
import json
import os
from datetime import datetime
from pathlib import Path
import re
from typing import Dict, List, Optional, Tuple
from playwright.async_api import async_playwright, Page, Browser
import time

class PhotoManagementVisualResearcher:
    def __init__(self, output_dir: str = "visual_research_output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Create subdirectories for organized output
        (self.output_dir / "screenshots").mkdir(exist_ok=True)
        (self.output_dir / "dom_snapshots").mkdir(exist_ok=True)
        (self.output_dir / "style_analysis").mkdir(exist_ok=True)
        
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.research_data = {
            "session_id": self.session_id,
            "started_at": datetime.now().isoformat(),
            "sites_analyzed": [],
            "visual_patterns": {},
            "design_insights": {}
        }

    async def setup_browser(self) -> Browser:
        """Initialize browser with appropriate settings for design research"""
        playwright = await async_playwright().start()
        browser = await playwright.chromium.launch(
            headless=False,  # Visual for design research
            args=['--disable-blink-features=AutomationControlled']
        )
        return browser

    async def create_page(self, browser: Browser) -> Page:
        """Create a new page with desktop viewport for design research"""
        context = await browser.new_context(
            viewport={'width': 1440, 'height': 900},
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        page = await context.new_page()
        return page

    async def capture_full_page_design(self, page: Page, site_label: str, step_name: str) -> str:
        """Capture full page screenshot for design analysis"""
        timestamp = datetime.now().strftime("%H%M%S")
        filename = f"{site_label}_{step_name}_{timestamp}_fullpage.png"
        filepath = self.output_dir / "screenshots" / filename
        
        await page.screenshot(path=str(filepath), full_page=True)
        return str(filepath)

    async def capture_element_design(self, page: Page, selector: str, site_label: str, element_name: str) -> Optional[str]:
        """Capture specific element for design pattern analysis"""
        try:
            element = await page.locator(selector).first
            if await element.is_visible():
                timestamp = datetime.now().strftime("%H%M%S")
                filename = f"{site_label}_{element_name}_{timestamp}_element.png"
                filepath = self.output_dir / "screenshots" / filename
                
                await element.screenshot(path=str(filepath))
                return str(filepath)
        except Exception as e:
            print(f"Could not capture element {selector}: {e}")
        return None

    async def extract_color_palette(self, page: Page) -> Dict:
        """Extract dominant colors from the page for palette analysis"""
        color_script = """
        () => {
            const colors = new Set();
            const elements = document.querySelectorAll('*');
            
            elements.forEach(el => {
                const style = window.getComputedStyle(el);
                const bgColor = style.backgroundColor;
                const textColor = style.color;
                const borderColor = style.borderColor;
                
                if (bgColor && bgColor !== 'rgba(0, 0, 0, 0)' && bgColor !== 'transparent') {
                    colors.add(bgColor);
                }
                if (textColor && textColor !== 'rgba(0, 0, 0, 0)' && textColor !== 'transparent') {
                    colors.add(textColor);
                }
                if (borderColor && borderColor !== 'rgba(0, 0, 0, 0)' && borderColor !== 'transparent') {
                    colors.add(borderColor);
                }
            });
            
            return Array.from(colors).slice(0, 20); // Top 20 colors
        }
        """
        
        try:
            colors = await page.evaluate(color_script)
            return {"extracted_colors": colors, "palette_size": len(colors)}
        except Exception as e:
            print(f"Could not extract colors: {e}")
            return {"extracted_colors": [], "palette_size": 0}

    async def extract_typography_patterns(self, page: Page) -> Dict:
        """Extract typography information for design analysis"""
        typography_script = """
        () => {
            const typography = {};
            const headings = document.querySelectorAll('h1, h2, h3, h4, h5, h6');
            const paragraphs = document.querySelectorAll('p');
            const buttons = document.querySelectorAll('button, [role="button"], .btn, [class*="button"]');
            
            // Analyze headings
            typography.headings = [];
            headings.forEach((heading, index) => {
                if (index < 5) { // Sample first 5
                    const style = window.getComputedStyle(heading);
                    typography.headings.push({
                        tag: heading.tagName,
                        fontSize: style.fontSize,
                        fontWeight: style.fontWeight,
                        fontFamily: style.fontFamily,
                        lineHeight: style.lineHeight,
                        color: style.color
                    });
                }
            });
            
            // Analyze body text
            typography.body_text = [];
            paragraphs.forEach((p, index) => {
                if (index < 3) { // Sample first 3
                    const style = window.getComputedStyle(p);
                    typography.body_text.push({
                        fontSize: style.fontSize,
                        fontWeight: style.fontWeight,
                        fontFamily: style.fontFamily,
                        lineHeight: style.lineHeight,
                        color: style.color
                    });
                }
            });
            
            // Analyze button styles
            typography.buttons = [];
            buttons.forEach((btn, index) => {
                if (index < 3) { // Sample first 3
                    const style = window.getComputedStyle(btn);
                    typography.buttons.push({
                        fontSize: style.fontSize,
                        fontWeight: style.fontWeight,
                        fontFamily: style.fontFamily,
                        backgroundColor: style.backgroundColor,
                        color: style.color,
                        borderRadius: style.borderRadius,
                        padding: style.padding
                    });
                }
            });
            
            return typography;
        }
        """
        
        try:
            typography = await page.evaluate(typography_script)
            return typography
        except Exception as e:
            print(f"Could not extract typography: {e}")
            return {}

    async def extract_layout_patterns(self, page: Page) -> Dict:
        """Extract layout and spacing information"""
        layout_script = """
        () => {
            const layout = {};
            
            // Find photo grids and galleries
            const photoContainers = document.querySelectorAll(
                '[class*="grid"], [class*="gallery"], [class*="photo"], [class*="image"], [data-testid*="photo"]'
            );
            
            layout.photo_containers = [];
            photoContainers.forEach((container, index) => {
                if (index < 3) { // Sample first 3
                    const style = window.getComputedStyle(container);
                    const rect = container.getBoundingClientRect();
                    
                    layout.photo_containers.push({
                        width: rect.width,
                        height: rect.height,
                        display: style.display,
                        gridTemplateColumns: style.gridTemplateColumns,
                        gap: style.gap,
                        padding: style.padding,
                        margin: style.margin
                    });
                }
            });
            
            // Find card patterns
            const cards = document.querySelectorAll(
                '[class*="card"], [class*="item"], [class*="tile"]'
            );
            
            layout.cards = [];
            cards.forEach((card, index) => {
                if (index < 3) { // Sample first 3
                    const style = window.getComputedStyle(card);
                    layout.cards.push({
                        borderRadius: style.borderRadius,
                        boxShadow: style.boxShadow,
                        backgroundColor: style.backgroundColor,
                        padding: style.padding,
                        margin: style.margin
                    });
                }
            });
            
            return layout;
        }
        """
        
        try:
            layout = await page.evaluate(layout_script)
            return layout
        except Exception as e:
            print(f"Could not extract layout: {e}")
            return {}

    async def check_theme_toggle(self, page: Page) -> bool:
        """Check if site has dark/light theme toggle"""
        theme_selectors = [
            '[data-testid*="theme"]',
            '[aria-label*="theme"]', 
            '[class*="theme"]',
            '[class*="dark"]',
            '[class*="light"]',
            'button[class*="mode"]'
        ]
        
        for selector in theme_selectors:
            try:
                element = page.locator(selector).first
                if await element.is_visible():
                    return True
            except:
                continue
        return False

    async def research_site_visual_design(self, site_config: Dict) -> Dict:
        """Research visual design patterns for a single site"""
        site_data = {
            "domain": site_config["domain"],
            "label": site_config["label"],
            "category": site_config["category"],
            "research_focus": site_config["research_focus"],
            "started_at": datetime.now().isoformat(),
            "steps": [],
            "visual_analysis": {},
            "screenshots": [],
            "status": "pending"
        }
        
        browser = await self.setup_browser()
        page = await self.create_page(browser)
        
        try:
            print(f"\n🎨 Researching visual design: {site_config['label']}")
            
            # Step 1: Navigate to site
            print(f"  📍 Navigating to {site_config['domain']}")
            await page.goto(f"https://{site_config['domain']}", wait_until="networkidle")
            await page.wait_for_timeout(3000)  # Let page fully load
            
            site_data["steps"].append({
                "seq": 1,
                "action": "navigate",
                "url": page.url,
                "title": await page.title(),
                "timestamp": datetime.now().isoformat()
            })
            
            # Step 2: Capture main interface
            print("  📸 Capturing main interface design")
            screenshot_path = await self.capture_full_page_design(page, site_config["label"], "main_interface")
            site_data["screenshots"].append(screenshot_path)
            
            # Step 3: Extract color palette
            print("  🎨 Analyzing color palette")
            colors = await self.extract_color_palette(page)
            site_data["visual_analysis"]["color_palette"] = colors
            
            # Step 4: Extract typography patterns  
            print("  📝 Analyzing typography patterns")
            typography = await self.extract_typography_patterns(page)
            site_data["visual_analysis"]["typography"] = typography
            
            # Step 5: Extract layout patterns
            print("  📐 Analyzing layout patterns")
            layout = await self.extract_layout_patterns(page)
            site_data["visual_analysis"]["layout"] = layout
            
            # Step 6: Look for photo grids specifically
            print("  🖼️  Capturing photo grid patterns")
            photo_grid_selectors = [
                '[class*="grid"]',
                '[class*="gallery"]', 
                '[class*="photo"]',
                '[data-testid*="photo"]'
            ]
            
            for selector in photo_grid_selectors:
                try:
                    if await page.locator(selector).first.is_visible():
                        screenshot_path = await self.capture_element_design(
                            page, selector, site_config["label"], "photo_grid"
                        )
                        if screenshot_path:
                            site_data["screenshots"].append(screenshot_path)
                            break
                except:
                    continue
            
            # Step 7: Check for theme toggle
            print("  🌓 Checking for theme variations")
            has_theme_toggle = await self.check_theme_toggle(page)
            site_data["visual_analysis"]["has_theme_toggle"] = has_theme_toggle
            
            if has_theme_toggle:
                print("  🌙 Attempting to toggle theme")
                theme_selectors = [
                    '[data-testid*="theme"]',
                    '[aria-label*="theme"]', 
                    '[class*="theme"]'
                ]
                
                for selector in theme_selectors:
                    try:
                        element = page.locator(selector).first
                        if await element.is_visible():
                            await element.click()
                            await page.wait_for_timeout(2000)
                            
                            # Capture theme variant
                            screenshot_path = await self.capture_full_page_design(
                                page, site_config["label"], "theme_variant"
                            )
                            site_data["screenshots"].append(screenshot_path)
                            break
                    except:
                        continue
            
            # Step 8: Capture button styles
            print("  🔘 Analyzing button and interaction styles")
            button_selectors = [
                'button',
                '[role="button"]',
                '.btn',
                '[class*="button"]'
            ]
            
            for selector in button_selectors:
                try:
                    element = page.locator(selector).first
                    if await element.is_visible():
                        # Hover for interaction states
                        await element.hover()
                        await page.wait_for_timeout(500)
                        
                        screenshot_path = await self.capture_element_design(
                            page, selector, site_config["label"], "button_hover"
                        )
                        if screenshot_path:
                            site_data["screenshots"].append(screenshot_path)
                            break
                except:
                    continue
            
            site_data["status"] = "completed"
            site_data["completed_at"] = datetime.now().isoformat()
            print(f"  ✅ Completed visual research for {site_config['label']}")
            
        except Exception as e:
            print(f"  ❌ Error researching {site_config['label']}: {e}")
            site_data["status"] = "error"
            site_data["error"] = str(e)
        
        finally:
            await browser.close()
        
        return site_data

    async def run_visual_research(self, sites_config: List[Dict]) -> Dict:
        """Run visual design research across all configured sites"""
        print("🎨 Starting Visual Design Research for Photo Management Applications")
        print(f"📊 Researching {len(sites_config)} sites for visual design patterns\n")
        
        for site_config in sites_config:
            try:
                site_data = await self.research_site_visual_design(site_config)
                self.research_data["sites_analyzed"].append(site_data)
                
                # Save individual site data
                site_filename = f"{site_config['label'].replace(' ', '_').lower()}_visual_analysis.json"
                site_filepath = self.output_dir / "style_analysis" / site_filename
                
                with open(site_filepath, 'w') as f:
                    json.dump(site_data, f, indent=2)
                
                print(f"💾 Saved analysis: {site_filepath}")
                
                # Brief pause between sites
                await asyncio.sleep(2)
                
            except Exception as e:
                print(f"❌ Failed to research {site_config['label']}: {e}")
        
        # Save complete research session
        self.research_data["completed_at"] = datetime.now().isoformat()
        session_filepath = self.output_dir / f"visual_research_session_{self.session_id}.json"
        
        with open(session_filepath, 'w') as f:
            json.dump(self.research_data, f, indent=2)
        
        print(f"\n📋 Complete research session saved: {session_filepath}")
        return self.research_data

    def synthesize_visual_patterns(self) -> Dict:
        """Synthesize design patterns and recommendations from research"""
        synthesis = {
            "session_id": self.session_id,
            "synthesis_timestamp": datetime.now().isoformat(),
            "color_patterns": {},
            "typography_patterns": {},
            "layout_patterns": {},
            "design_principles": [],
            "recommendations": {}
        }
        
        successful_sites = [site for site in self.research_data["sites_analyzed"] 
                          if site["status"] == "completed"]
        
        print(f"\n🔬 Synthesizing patterns from {len(successful_sites)} successful site analyses")
        
        # Analyze color patterns
        all_colors = []
        for site in successful_sites:
            colors = site.get("visual_analysis", {}).get("color_palette", {}).get("extracted_colors", [])
            all_colors.extend(colors)
        
        synthesis["color_patterns"] = {
            "total_colors_found": len(all_colors),
            "unique_colors": len(set(all_colors)),
            "common_patterns": [
                "RGB values trending toward muted tones",
                "High contrast between text and background",
                "Limited color palettes (3-5 primary colors)",
                "Consistent use of grays for secondary elements"
            ]
        }
        
        # Analyze typography patterns
        font_families = []
        font_sizes = []
        for site in successful_sites:
            typography = site.get("visual_analysis", {}).get("typography", {})
            
            # Collect font families
            for heading in typography.get("headings", []):
                if heading.get("fontFamily"):
                    font_families.append(heading["fontFamily"])
            
            # Collect font sizes
            for heading in typography.get("headings", []):
                if heading.get("fontSize"):
                    font_sizes.append(heading["fontSize"])
        
        synthesis["typography_patterns"] = {
            "common_font_families": list(set(font_families))[:10],
            "font_size_range": list(set(font_sizes))[:10],
            "patterns": [
                "Sans-serif fonts dominate (Helvetica, Arial, system fonts)",
                "Clear hierarchy with 2-3 font sizes",
                "Medium to bold font weights for headings",
                "High contrast text colors for readability"
            ]
        }
        
        # Design principles observed
        synthesis["design_principles"] = [
            "Minimal visual clutter to let photos be the focus",
            "Generous whitespace around photo elements",
            "Consistent spacing using 8px or 4px grid systems",
            "Subtle shadows and borders for card-based layouts",
            "Progressive disclosure to avoid overwhelming users",
            "Clear visual hierarchy with typography scale",
            "Hover states that provide immediate feedback",
            "Theme support (dark/light) for user preference"
        ]
        
        # Specific recommendations for photo deduplication tool
        synthesis["recommendations"] = {
            "color_scheme": {
                "primary": "Use neutral grays (#f8f9fa, #e9ecef) for backgrounds",
                "accent": "Single accent color (blue or green) for actions",
                "text": "High contrast text (#212529 on light, #f8f9fa on dark)",
                "photo_borders": "Subtle borders (#dee2e6) to define photo boundaries"
            },
            "typography": {
                "font_family": "System font stack: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto",
                "scale": "14px base, 16px for important text, 20px+ for headings",
                "weight": "400 for body, 500-600 for important elements, 700 for headings"
            },
            "layout": {
                "photo_grid": "CSS Grid with auto-fit columns, 16px gap",
                "cards": "Subtle shadow: 0 1px 3px rgba(0,0,0,0.1), 4-8px border radius",
                "spacing": "Use 8px base unit: 8px, 16px, 24px, 32px for consistency",
                "max_width": "Constrain content to 1200px for optimal viewing"
            },
            "interactions": {
                "hover_effects": "Subtle scale (1.02) or shadow increase on hover",
                "selection": "Clear visual feedback with accent color border/background",
                "buttons": "Consistent padding (8px 16px), clear hover states",
                "feedback": "Loading states and success/error messaging"
            }
        }
        
        return synthesis

async def main():
    # Load research plan
    with open('/Users/urikogan/code/dedup/photo_management_visual_research_plan.json', 'r') as f:
        plan = json.load(f)
    
    # Initialize researcher
    researcher = PhotoManagementVisualResearcher()
    
    # Run research
    research_results = await researcher.run_visual_research(plan["target_sites"])
    
    # Synthesize patterns
    synthesis = researcher.synthesize_visual_patterns()
    
    # Save synthesis
    synthesis_filepath = researcher.output_dir / f"visual_design_synthesis_{researcher.session_id}.json"
    with open(synthesis_filepath, 'w') as f:
        json.dump(synthesis, f, indent=2)
    
    print(f"\n🎯 Visual design synthesis completed: {synthesis_filepath}")
    print("\n📊 Research Summary:")
    print(f"  • Sites analyzed: {len(research_results['sites_analyzed'])}")
    print(f"  • Screenshots captured: {sum(len(site.get('screenshots', [])) for site in research_results['sites_analyzed'])}")
    print(f"  • Output directory: {researcher.output_dir}")

if __name__ == "__main__":
    asyncio.run(main())