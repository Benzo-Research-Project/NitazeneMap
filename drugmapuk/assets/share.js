// Share button
document.body.addEventListener('click', async (event) => {
    const button = event.target.closest('.shareButton');
    
    if (button) {
        const title = "DrugMapUK | National Supply Monitoring Dashboard";
        const url = "https://brp.org.uk"; // update before launch

        if (navigator.share) {
            try {
                await navigator.share({ title, url });
                console.log('Thanks for sharing!');
            } catch (err) {
                console.log('Share cancelled or failed:', err);
            }
            return;
        }

        const shareUrl = `https://twitter.com{encodeURIComponent(url)}`;
        window.open(shareUrl, '_blank');
    }
});
