import { test, expect } from '@playwright/test';

test('ブログ投稿先選択UIの表示と操作', async ({ page }) => {
  await page.setContent(`
    <div style="border:1px solid #ccc;padding:20px;width:300px;margin:40px auto;text-align:center;">
      <h3>投稿先ブログを選択</h3>
      <button id="blog1">Blog1</button>
      <button id="blog2">Blog2</button>
      <button id="blog3">Blog3</button>
      <button id="multi">複数選択</button>
      <div id="result" style="margin-top:20px;color:green;"></div>
    </div>
    <script>
      document.getElementById('blog1').onclick = () => {
        document.getElementById('result').textContent = 'Blog1に投稿します';
      };
      document.getElementById('blog2').onclick = () => {
        document.getElementById('result').textContent = 'Blog2に投稿します';
      };
      document.getElementById('blog3').onclick = () => {
        document.getElementById('result').textContent = 'Blog3に投稿します';
      };
      document.getElementById('multi').onclick = () => {
        document.getElementById('result').textContent = '複数ブログに投稿します';
      };
    </script>
  `);

  await expect(page.locator('h3')).toHaveText('投稿先ブログを選択');
  await page.click('#blog1');
  await expect(page.locator('#result')).toHaveText('Blog1に投稿します');
  await page.click('#multi');
  await expect(page.locator('#result')).toHaveText('複数ブログに投稿します');
});