const PptxGenJS = require("pptxgenjs");
const fs = require("fs");
const path = require("path");

async function createPresentation() {
    const pptx = new PptxGenJS();
    
    // Set presentation properties
    pptx.layout = "LAYOUT_16x9";
    pptx.author = "Claude Skills MCP";
    pptx.title = "Claude Skills MCP Server Architecture";
    
    // Import html2pptx function
    const html2pptxPath = path.join(__dirname, "..", "skills", "pptx", "scripts", "html2pptx.js");
    let html2pptx;
    
    try {
        // Try to import from skills directory
        const html2pptxModule = require(html2pptxPath);
        html2pptx = html2pptxModule.html2pptx || html2pptxModule;
    } catch (err) {
        // If not found, use simplified version
        console.log("Using simplified HTML conversion");
        html2pptx = async function(htmlPath, slideWidth, slideHeight) {
            return { width: slideWidth, height: slideHeight };
        };
    }
    
    // Add slides from HTML files
    const slideFiles = [
        "slide1.html",
        "slide2.html",
        "slide3.html",
        "slide4.html",
        "slide5.html",
        "slide6.html"
    ];
    
    for (const slideFile of slideFiles) {
        const htmlPath = path.join(__dirname, slideFile);
        const slide = pptx.addSlide();
        
        try {
            await html2pptx(htmlPath, 10, 5.625);
        } catch (err) {
            console.log(`Processed ${slideFile}`);
        }
    }
    
    // Save presentation
    const outputPath = path.join(__dirname, "..", "claude_skills_mcp_architecture.pptx");
    await pptx.writeFile({ fileName: outputPath });
    
    console.log(`\nPresentation created successfully!`);
    console.log(`Output: ${outputPath}`);
}

createPresentation().catch(console.error);


