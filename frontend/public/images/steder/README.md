# Photos of places

Upload photos here (GitHub: **Add file → Upload files**), then register each one
in `frontend/src/lib/images.ts` with real alt text.

Name the file after the page slug — the last segment of the URL:

    https://www.aalumvej26.dk/oplevelser/lodbjerg-fyr-klatr-.../
                                         ^^^^^^^^^^^^^^^^^^^^ this

Only add a photo that genuinely shows the place. A registered image is published
as schema.org `image`, which asserts that the picture depicts that subject. A
page with no entry simply gets no image in its structured data — that is a
correct outcome, not a gap to fill with a stock shot.

Landscape, ideally 1600px wide or more. The build warns if a registered file is
missing, if its slug no longer matches a page, or if alt text is empty.
