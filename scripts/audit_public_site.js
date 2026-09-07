// Validate published pages, their local destinations and the Amplify asset allowlist.
const fs = require('node:fs');
const path = require('node:path');

const root = path.resolve(__dirname, '..');
const read = (file) => fs.readFileSync(path.join(root, file), 'utf8');
const pages = ['', 'articles', 'guides'].flatMap((dir) => fs.readdirSync(path.join(root, dir))
    .filter((name) => name.endsWith('.html')).map((name) => dir ? `${dir}/${name}` : name));
const patterns = [...read('amplify.yml').matchAll(/^\s+- '([^']+)'/gm)].map((match) =>
    new RegExp('^' + match[1].split('*').map((part) => part.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')).join('[^/]*') + '$'));
const deployed = (file) => patterns.some((pattern) => pattern.test(file));
const sitemapUrls = new Set([...read('sitemap.xml').matchAll(/<loc>([^<]+)<\/loc>/g)].map((match) => match[1]));
const errors = [];
const assets = new Set();
const pageSource = new Map(pages.map((file) => [file, read(file)]));

for (const [file, html] of pageSource) {
    const markup = html.replace(/(<(script|style)\b[^>]*>)[\s\S]*?<\/\2>/gi, '$1</$2>');
    if (!deployed(file)) errors.push(`${file}: page excluded from deployment`);
    const head = html.match(/<head>[\s\S]*?<\/head>/i)?.[0] || '';
    const canonical = head.match(/<link rel="canonical" href="([^"]+)"/)?.[1];
    if (!/name="robots" content="[^"]*noindex/.test(head)) {
        if (!canonical) errors.push(`${file}: missing canonical URL`);
        else if (!sitemapUrls.has(canonical)) errors.push(`${file}: canonical missing from sitemap: ${canonical}`);
    }
    if (file.startsWith('articles/') && !['articles/index.html', 'articles/market.html'].includes(file)) {
        const footer = markup.match(/<footer\b[\s\S]*?<\/footer>/)?.[0] || '';
        for (const destination of ['about.html', 'contact.html', 'privacy.html', 'terms.html']) {
            if (!footer.includes(destination)) errors.push(`${file}: missing footer link ${destination}`);
        }
    }
    const ids = [...markup.matchAll(/\bid="([^"]+)"/g)].map((match) => match[1]);
    if (new Set(ids).size !== ids.length) errors.push(`${file}: duplicate HTML id`);
    for (const match of markup.matchAll(/\b(?:href|src)="([^"]+)"/g)) {
        const address = match[1].replace(/&amp;/g, '&');
        if (/^[a-z][a-z0-9+.-]*:|^\/\//i.test(address)) continue;
        const url = new URL(address, `https://www.hpmplab.com/${file}`);
        let destination = decodeURIComponent(url.pathname).slice(1);
        if (destination.endsWith('/') || !destination) destination += 'index.html';
        if (!fs.existsSync(path.join(root, destination))) {
            errors.push(`${file}: missing local destination ${address}`);
            continue;
        }
        if (!deployed(destination)) errors.push(`${file}: destination excluded from deployment ${address}`);
        if (!destination.endsWith('.html')) assets.add(destination);
        // Tool pages can create fragment targets after initialization.
        if (url.hash && pageSource.has(destination) && destination !== 'app.html') {
            const id = decodeURIComponent(url.hash.slice(1));
            if (!pageSource.get(destination).includes(`id="${id}"`) && !pageSource.get(destination).includes(`name="${id}"`)) {
                errors.push(`${file}: missing fragment ${address}`);
            }
        }
    }
}

if (errors.length) {
    console.error(errors.join('\n'));
    process.exitCode = 1;
} else {
    console.log(`public site audit: ${pages.length} pages, ${assets.size} local assets, links and deployment paths valid`);
}
