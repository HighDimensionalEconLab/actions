# Release Notes

## v1.4.2

Fix blank pages in Playwright PDF generation caused by RevealJS print-pdf
mode setting `display: inline-block` on slide children. Chromium's print
engine treats inline-block as an atomic box that cannot split across page
boundaries, producing blank pages when combined with the RevealJS margin.

## v1.4.1

This release includes updates and bug fixes.