const fs = require('fs');
const path = require('path');

function walk(dir) {
    let results = [];
    const list = fs.readdirSync(dir);
    list.forEach(file => {
        file = path.join(dir, file);
        const stat = fs.statSync(file);
        if (stat && stat.isDirectory()) {
            results = results.concat(walk(file));
        } else if (file.endsWith('.vue') || file.endsWith('.css')) {
            results.push(file);
        }
    });
    return results;
}

const files = walk('C:/DoAnTotNghiep/V-Shield/View/src');
let count = 0;

const replacements = [
    { from: /60,\s*205,\s*215/g, to: '79, 104, 255' },
    { from: /63,\s*196,\s*205/g, to: '21, 76, 255' },
    { from: /#3ccdd7/ig, to: '#4f68ff' },
    { from: /#3fc4cd/ig, to: '#154cff' },
    { from: /#041b1c/ig, to: '#000a3d' },
    { from: /#35e7f2/ig, to: '#b4bbff' },
    { from: /#d3ffff/ig, to: '#eff0ff' },
    { from: /#38d3dd/ig, to: '#949eff' },
    { from: /var\(--java-/g, to: 'var(--blue-ribbon-' }
];

files.forEach(file => {
    let content = fs.readFileSync(file, 'utf8');
    let original = content;
    
    replacements.forEach(r => {
        content = content.replace(r.from, r.to);
    });

    if (content !== original) {
        fs.writeFileSync(file, content);
        console.log('Updated ' + file);
        count++;
    }
});

console.log('Total files updated: ' + count);
