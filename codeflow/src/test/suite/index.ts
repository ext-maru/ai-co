import * as path from 'path';
import Mocha from 'mocha';
import { glob } from 'glob';

export async function run(): Promise<void> {
    // Create the mocha test
    const mocha = new Mocha({
        ui: 'tdd',
        color: true
    });

    const testsRoot = path.resolve(__dirname, '..');

    try {
        // Use glob.sync instead of async glob
        const files = await new Promise<string[]>((resolve, reject) => {
            glob('**/**.test.js', { cwd: testsRoot }, (err: Error | null, files: string[]) => {
                if (err) {
                    reject(err);
                } else {
                    resolve(files);
                }
            });
        });
        
        // Add files to the test suite
        files.forEach((f: string) => mocha.addFile(path.resolve(testsRoot, f)));

        // Run the mocha test
        return new Promise((resolve, reject) => {
            mocha.run((failures: number) => {
                if (failures > 0) {
                    reject(new Error(`${failures} tests failed.`));
                } else {
                    resolve();
                }
            });
        });
    } catch (err) {
        console.error(err);
        throw err;
    }
}