// buildPhotoPagesData.js
// Run this script from the /js folder.
// This script builds a JSON file containing PhotoPages data from infotable.json.
// It reads each infotable record, extracts the necessary fields (name, pic, born) and writes it to PhotoPagesData.json along with the contents of the text file pointed to by the bio field.
// The infotable is expected to have fields: pic, name and born.
// If a record is missing any of these fields, it is skipped.
// If a record has a duplicate pic, it is also skipped.
// The bio field is optional; if it exists, the script reads the corresponding text file and
// includes its contents in the output JSON.  If it doesn't exist, a default message is written to bioText.
// The output file is used in the PhotoPages.html to display the family photo gallery.

import infoTable from '../data/infotable.json' with { type: 'json' };
import fs from 'fs/promises';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const bioDir = path.join(__dirname, '../bios');
const outputPath = path.join(__dirname, '../data/PhotoPagesData.json');

const photos = [];

async function readText(fname) {
  try {
    const fullPath = path.join(bioDir, fname);
    const data = await fs.readFile(fullPath, 'utf8');
    return data;
  } catch (error) {
    console.error(`Error loading bio "${fname}":`, error.message);
    return null;
  }
}

async function buildPhotoPagesData() {
  for (const record of infoTable) {
    if (!record.pic   || !record.name || !record.born ) {
      console.warn(`Skipping record with missing fields: ${JSON.stringify(record.name)}`);
      continue;
    }
    // Skip records with duplicate .pic
    const duplicate = photos.some(p => p.pic === record.pic);
    if (duplicate) continue;

    let bioText = `The bio for ${record.name} should be updated soon.`;

    if (record.bio) {
      const fetchedBio = await readText(record.bio);
      if (fetchedBio) bioText = fetchedBio;
    }

    photos.push({
      pic: record.pic,
      name: record.name,
      born: record.born,
      bioText // changed from bio to bioText
    });
  }

  // Write to static JSON file
  await fs.writeFile(outputPath, JSON.stringify(photos, null, 2));
  console.log(`✅ PhotoPages exported to: ${outputPath}`);
}

await buildPhotoPagesData();