$base = "C:\Users\Sreekar_Tirumala\Documents\College\IS\IS-project"
$pptxPath = Join-Path $base "TreasureCache_Presentation.pptx"
$pdfPath = Join-Path $base "TreasureCache_Presentation.pdf"

Write-Host "Opening PowerPoint..."
$ppt = New-Object -ComObject PowerPoint.Application
Write-Host "Opening presentation..."
$pres = $ppt.Presentations.Open($pptxPath, 2, 0, 0)
Write-Host "Exporting to PDF..."
$pres.SaveAs($pdfPath, 32) # 32 = ppSaveAsPDF
$pres.Close()
$ppt.Quit()
Write-Host "Successfully exported TreasureCache_Presentation.pdf"
