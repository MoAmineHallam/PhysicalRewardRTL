param(
    [string]$TemplatePath = "",
    [string]$SourcePath = "thesis/proposal/proposal_draft.md",
    [string]$OutputPath = "thesis/proposal/HIT_Master_Thesis_Proposal_Mohamed_Amine_Hallam.docx",
    [string]$PreviewPdfPath = "thesis/proposal/HIT_Master_Thesis_Proposal_Mohamed_Amine_Hallam_preview.pdf",
    [string]$School = "[TO BE COMPLETED]",
    [string]$Major = "[TO BE COMPLETED]",
    [string]$Supervisor = "Professor Tseng",
    [string]$StudentId = "[TO BE COMPLETED]"
)

$ErrorActionPreference = "Stop"

$repo = (Resolve-Path -LiteralPath ".").Path
if (-not $TemplatePath) {
    $template = Get-ChildItem -LiteralPath (Join-Path $repo "thesis/requirements") -Filter "*.docx" |
        Select-Object -First 1
    if ($null -eq $template) {
        throw "No Word template was found in thesis/requirements."
    }
    $TemplatePath = $template.FullName
}

$sourceFull = (Resolve-Path -LiteralPath $SourcePath).Path
$templateFull = (Resolve-Path -LiteralPath $TemplatePath).Path
$outputFull = Join-Path $repo $OutputPath
$previewFull = Join-Path $repo $PreviewPdfPath
$outputDir = Split-Path -Parent $outputFull
New-Item -ItemType Directory -Force -Path $outputDir | Out-Null
Copy-Item -LiteralPath $templateFull -Destination $outputFull -Force

$title = "Hardware-Aware LLM Architectures for FPGA RTL Generation: Inference Efficiency and Failure-Aware Utility under Fixed Budgets"
$word = $null
$doc = $null

function Replace-AllText {
    param([object]$Document, [string]$FindText, [string]$ReplaceText)
    $range = $Document.Content
    $find = $range.Find
    $find.ClearFormatting()
    $find.Replacement.ClearFormatting()
    $replaced = $find.Execute($FindText, $false, $false, $false, $false, $false,
        $true, 1, $false, $ReplaceText, 2)
    if (-not $replaced) {
        throw "Template text was not found: $FindText"
    }
}

try {
    $word = New-Object -ComObject Word.Application
    $word.Visible = $false
    $word.DisplayAlerts = 0
    $doc = $word.Documents.Open($outputFull)

    Replace-AllText $doc "Title: Trajectory Planning for Coordinated Motion of Dual-Armed Robotic Astronauts" "Title: $title"
    Replace-AllText $doc "School:               School of  XXXXX          " "School:                    $School"
    Replace-AllText $doc "Major:                Mechanical Engineering      " "Major:                     $Major"
    Replace-AllText $doc "Supervisor:             Professor Xu XX            " "Supervisor:                $Supervisor"
    Replace-AllText $doc "Graduate Student:            **                   " "Graduate Student:          Mohamed Amine Hallam"
    Replace-AllText $doc "Student ID:                15S1530**             " "Student ID:                $StudentId"
    Replace-AllText $doc "Date:                     September 23, 2016       " "Date:                      September 4, 2026"
    Replace-AllText $doc "(Template)" ""

    # The distributed template contains three manual page breaks around its
    # section breaks, which otherwise create an empty page before the contents.
    # Remove only manual page breaks; the cover/contents/body section breaks
    # remain intact and proposal page breaks are inserted later below.
    $manualBreakRange = $doc.Content
    $manualBreakFind = $manualBreakRange.Find
    $manualBreakFind.ClearFormatting()
    $manualBreakFind.Replacement.ClearFormatting()
    $null = $manualBreakFind.Execute("^m", $false, $false, $false, $false, $false,
        $true, 1, $false, "", 2)

    $titleRange = $doc.Content
    $titleFind = $titleRange.Find
    $titleFind.Text = $title
    if ($titleFind.Execute()) {
        $titleRange.Font.Name = "Times New Roman"
        $titleRange.Font.Size = 12
        $titleRange.Font.Bold = $true
    }

    if ($doc.Sections.Count -lt 3) {
        throw "The template must retain its three-section cover/contents/body layout."
    }

    # Replace only the body of section 3, preserving its section settings,
    # header, footer, and final paragraph mark.
    $section3 = $doc.Sections.Item(3)
    $bodyStart = $section3.Range.Start
    $bodyClear = $doc.Range($bodyStart, $section3.Range.End - 1)
    $bodyClear.Delete() | Out-Null
    $script:insertPos = $bodyStart
    $script:firstHeading = $true
    $script:inReferences = $false

    function Add-ProposalParagraph {
        param(
            [string]$Text,
            [string]$Style = "Body Text First Indent",
            [switch]$Bullet,
            [switch]$Center,
            [switch]$Bold,
            [switch]$Italic,
            [switch]$Hanging
        )
        $start = $script:insertPos
        $range = $doc.Range($start, $start)
        $range.Text = $Text + "`r"
        $end = $range.End
        $paragraphRange = $doc.Range($start, $end)
        try { $paragraphRange.Style = $Style } catch { $paragraphRange.Style = "Normal" }
        $paragraphRange.Font.Name = "Times New Roman"
        $paragraphRange.Font.Color = -16777216
        if ($Style -eq "Heading 1") {
            $paragraphRange.Font.Size = 14
            $paragraphRange.Font.Bold = $true
        } elseif ($Style -eq "Heading 2") {
            $paragraphRange.Font.Size = 12
            $paragraphRange.Font.Bold = $true
        } elseif ($Style -eq "Heading 3") {
            $paragraphRange.Font.Size = 11
            $paragraphRange.Font.Bold = $true
        } elseif ($Style -eq "Plain Text") {
            $paragraphRange.Font.Size = 10
        } else {
            $paragraphRange.Font.Size = 11
        }
        if ($Bold) { $paragraphRange.Font.Bold = $true }
        if ($Italic) { $paragraphRange.Font.Italic = $true }
        if ($Center) { $paragraphRange.ParagraphFormat.Alignment = 1 }
        if ($Bullet) {
            $paragraphRange.ParagraphFormat.FirstLineIndent = 0
            $paragraphRange.ParagraphFormat.LeftIndent = 21
            $paragraphRange.ListFormat.ApplyBulletDefault()
        }
        if ($Hanging) {
            $paragraphRange.ParagraphFormat.LeftIndent = 21
            $paragraphRange.ParagraphFormat.FirstLineIndent = -21
        }
        $paragraphRange.ParagraphFormat.SpaceAfter = 6
        if (($Style -ne "Heading 1") -and ($Style -ne "Heading 2") -and ($Style -ne "Heading 3")) {
            $paragraphRange.ParagraphFormat.Alignment = if ($Center) { 1 } else { 3 }
            $paragraphRange.ParagraphFormat.LineSpacingRule = 1
        }
        $script:insertPos = $end
    }

    function Add-PageBreak {
        $range = $doc.Range($script:insertPos, $script:insertPos)
        $range.InsertBreak(7)
        $script:insertPos = $range.End
    }

    function Add-ProposalEquation {
        param([string]$Text)
        $start = $script:insertPos
        $range = $doc.Range($start, $start)
        $range.Text = $Text + "`r"
        $end = $range.End
        $equationRange = $doc.Range($start, $end - 1)
        try { $equationRange.Paragraphs.Item(1).Range.Style = "Normal" } catch {}
        $equationRange.Font.Name = "Cambria Math"
        $equationRange.Font.Size = 11
        $equationRange.Font.Color = -16777216
        $equationRange.ParagraphFormat.Alignment = 1
        $equationRange.ParagraphFormat.SpaceAfter = 6
        # Word's COM dispatcher may ignore the Range argument on the first
        # OMaths.Add call unless the same range is also the active selection.
        $equationRange.Select()
        $selectedRange = $word.Selection.Range
        $null = $word.Selection.OMaths.Add($selectedRange)
        if ($word.Selection.OMaths.Count -gt 0) {
            $word.Selection.OMaths.Item(1).BuildUp()
        }
        $script:insertPos = $equationRange.Paragraphs.Item(1).Range.End
    }

    function Add-ProposalTable {
        param([object[]]$Rows)
        if ($Rows.Count -lt 2) { return }
        $columnCount = $Rows[0].Count
        $tableRange = $doc.Range($script:insertPos, $script:insertPos)
        $table = $doc.Tables.Add($tableRange, $Rows.Count, $columnCount)
        for ($r = 0; $r -lt $Rows.Count; $r++) {
            for ($c = 0; $c -lt $columnCount; $c++) {
                $table.Cell($r + 1, $c + 1).Range.Text = [string]$Rows[$r][$c]
            }
        }
        $table.Borders.Enable = 1
        $table.Rows.AllowBreakAcrossPages = $false
        $table.Rows.Item(1).Range.Font.Bold = $true
        $table.Rows.Item(1).HeadingFormat = $true
        $table.Range.Font.Name = "Times New Roman"
        $table.Range.Font.Size = 9
        $table.Range.Font.Color = -16777216
        $table.Range.ParagraphFormat.SpaceAfter = 0
        $table.Range.ParagraphFormat.LineSpacingRule = 0
        $table.AutoFitBehavior(2)
        $script:insertPos = $table.Range.End
        $after = $doc.Range($script:insertPos, $script:insertPos)
        $after.Text = "`r"
        $script:insertPos = $after.End
    }

    $lines = Get-Content -LiteralPath $sourceFull -Encoding UTF8
    for ($i = 0; $i -lt $lines.Count; $i++) {
        $line = $lines[$i]
        if ([string]::IsNullOrWhiteSpace($line)) { continue }

        if ($line.StartsWith("|")) {
            $tableLines = New-Object System.Collections.Generic.List[string]
            while (($i -lt $lines.Count) -and $lines[$i].StartsWith("|")) {
                $tableLines.Add($lines[$i])
                $i++
            }
            $i--
            $rows = New-Object System.Collections.Generic.List[object]
            foreach ($tableLine in $tableLines) {
                $cells = $tableLine.Trim().Trim("|").Split("|") | ForEach-Object { $_.Trim() }
                $isSeparator = $true
                foreach ($cell in $cells) {
                    if ($cell -notmatch '^:?-{3,}:?$') { $isSeparator = $false; break }
                }
                if (-not $isSeparator) { $rows.Add([object[]]$cells) }
            }
            Add-ProposalTable -Rows $rows.ToArray()
            continue
        }

        if ($line.StartsWith("### ")) {
            Add-ProposalParagraph -Text $line.Substring(4) -Style "Heading 3"
            continue
        }
        if ($line.StartsWith("## ")) {
            Add-ProposalParagraph -Text $line.Substring(3) -Style "Heading 2"
            continue
        }
        if ($line.StartsWith("# ")) {
            if (-not $script:firstHeading) { Add-PageBreak }
            $headingText = $line.Substring(2)
            if ($headingText -eq "References") { $script:inReferences = $true }
            Add-ProposalParagraph -Text $headingText -Style "Heading 1"
            $script:firstHeading = $false
            continue
        }
        if ($line.StartsWith("- ")) {
            Add-ProposalParagraph -Text $line.Substring(2) -Style "Body Text First Indent" -Bullet
            continue
        }
        if ($line -match '^Table\s+\d+') {
            Add-ProposalParagraph -Text $line -Style "Normal" -Center -Bold
            continue
        }
        if ($line.StartsWith("EQ: ")) {
            Add-ProposalEquation -Text $line.Substring(4)
            continue
        }
        if ($script:inReferences -and ($line -match '^\[\d+\]')) {
            Add-ProposalParagraph -Text $line -Style "Plain Text" -Hanging
            continue
        }
        Add-ProposalParagraph -Text $line -Style "Body Text First Indent"
    }

    # Replace the static example contents with a live Word table of contents.
    $section2 = $doc.Sections.Item(2)
    $contentsStart = $section2.Range.Start
    $contentsClear = $doc.Range($contentsStart, $section2.Range.End - 1)
    $contentsClear.Delete() | Out-Null
    $contentsTitle = $doc.Range($contentsStart, $contentsStart)
    $contentsTitle.Text = "Contents`r"
    $contentsTitle.Style = "Normal"
    $contentsTitle.Font.Name = "Times New Roman"
    $contentsTitle.Font.Size = 16
    $contentsTitle.Font.Bold = $true
    $contentsTitle.ParagraphFormat.Alignment = 1
    $tocRange = $doc.Range($contentsTitle.End, $contentsTitle.End)
    $toc = $doc.TablesOfContents.Add($tocRange, $true, 1, 3)

    # Replace the example fixed footer with an actual centered page-number field.
    $footer = $section3.Footers.Item(1)
    $footer.LinkToPrevious = $false
    $footer.Range.Text = ""
    $footer.PageNumbers.RestartNumberingAtSection = $true
    $footer.PageNumbers.StartingNumber = 1
    $null = $footer.PageNumbers.Add(1, $true)

    foreach ($property in @(
        @{ Index = 1; Value = $title },
        @{ Index = 2; Value = "Master's thesis proposal" },
        @{ Index = 3; Value = "Mohamed Amine Hallam" }
    )) {
        try { $doc.BuiltInDocumentProperties.Item($property.Index).Value = $property.Value } catch {}
    }

    $doc.Fields.Update() | Out-Null
    if ($doc.TablesOfContents.Count -gt 0) {
        $doc.TablesOfContents.Item(1).Update() | Out-Null
    }
    $doc.Repaginate()
    $doc.SaveAs2($outputFull, 16)
    $doc.ExportAsFixedFormat($previewFull, 17)

    $pages = $doc.ComputeStatistics(2)
    $words = $doc.ComputeStatistics(0)
    Write-Output "OUTPUT=$outputFull"
    Write-Output "PREVIEW=$previewFull"
    Write-Output "PAGES=$pages"
    Write-Output "WORDS=$words"
    Write-Output "TABLES=$($doc.Tables.Count)"
    Write-Output "TOCS=$($doc.TablesOfContents.Count)"
    Write-Output "SECTIONS=$($doc.Sections.Count)"
}
finally {
    if ($null -ne $doc) {
        try { $doc.Close($false) } catch { Write-Warning $_.Exception.Message }
    }
    if ($null -ne $word) {
        try { $word.Quit() } catch {}
    }
    if ($null -ne $doc) { [Runtime.InteropServices.Marshal]::ReleaseComObject($doc) | Out-Null }
    if ($null -ne $word) { [Runtime.InteropServices.Marshal]::ReleaseComObject($word) | Out-Null }
    [GC]::Collect()
    [GC]::WaitForPendingFinalizers()
}
