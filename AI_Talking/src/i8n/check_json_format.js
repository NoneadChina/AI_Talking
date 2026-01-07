const fs = require('fs');
const path = require('path');

const directoryPath = './';

fs.readdir(directoryPath, (err, files) => {
    if (err) {
        console.error('Error reading directory:', err);
        return;
    }

    const jsonFiles = files.filter(file => path.extname(file) === '.json');
    
    jsonFiles.forEach(file => {
        const filePath = path.join(directoryPath, file);
        try {
            const content = fs.readFileSync(filePath, 'utf8');
            JSON.parse(content);
            console.log(`${file}: 格式正确`);
        } catch (error) {
            console.error(`${file}: 格式错误 - ${error.message}`);
        }
    });
});
