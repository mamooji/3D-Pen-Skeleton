import type { ReactNode } from "react";
import { APP_PATH, PRIVACY_PATH, SITE, TERMS_PATH } from "@/site";
import { Layout } from "./Layout";

// Change this whenever either page's substance changes.
const UPDATED = "September 30, 2026";

function LegalPage({ title, children }: { title: string; children: ReactNode }) {
  return (
    <Layout>
      <article className="mx-auto max-w-3xl px-4 py-14 leading-relaxed sm:px-6 sm:py-20">
        <h1 className="font-heading text-3xl font-semibold tracking-tight sm:text-4xl">{title}</h1>
        <p className="mt-3 text-sm text-muted-foreground">Last updated {UPDATED}</p>
        <div className="mt-10 space-y-4 [&_a]:underline [&_a]:underline-offset-4 [&_li]:ml-5 [&_ul]:list-disc [&_ul]:space-y-2">
          {children}
        </div>
      </article>
    </Layout>
  );
}

function H2({ children }: { children: ReactNode }) {
  return <h2 className="pt-6 font-heading text-xl font-semibold tracking-tight">{children}</h2>;
}

function Contact() {
  return <a href={`mailto:${SITE.contactEmail}`}>{SITE.contactEmail}</a>;
}

export function Privacy() {
  return (
    <LegalPage title="Privacy policy">
      <p>
        <strong>The short version:</strong> your photo is used only to make your template, and it's deleted
        automatically 6 hours after you last use it. There are no accounts, no ads, and we don't set any cookies. Visits are counted
        with privacy-friendly analytics that run on our own server and don't identify you.
      </p>

      <H2>Who runs {SITE.name}</H2>
      <p>
        {SITE.name} is run by {SITE.operator}, who is responsible for your data here. Questions or requests go to{" "}
        <Contact />.
      </p>

      <H2>Your photos</H2>
      <p>
        Your browser shrinks the photo to at most 1600 pixels on its longest side, then sends it to our server. The
        server cuts out the object and builds the shape your template is made from.
      </p>
      <ul>
        <li>
          We keep the processed photo (its pixels, the cut-out, and the shape) so you can keep adjusting the template.
          It's deleted automatically 6 hours after you last use it.
        </li>
        <li>Your PDF is made on the server and sent straight to you. We don't keep a copy.</li>
        <li>
          We don't look at your photos, share them, sell them, or use them to train any model. They're linked only to a
          code made from the image itself, never to you.
        </li>
        <li>
          The app is meant for photos of objects. Please don't upload photos of people, or anything you'd rather no
          server ever saw.
        </li>
      </ul>

      <H2>Visitor statistics</H2>
      <p>
        We count visits with <a href="https://umami.is" target="_blank" rel="noopener">Umami</a>, which we run on our
        own server, so this data never goes to a third party. It records:
      </p>
      <ul>
        <li>which pages are viewed and the site you came from</li>
        <li>your browser, operating system, device type, screen size, and language</li>
        <li>your approximate location (country, region, and city), looked up from your IP address</li>
        <li>a few actions: uploading a photo, downloading a PDF, and clicking a Ko-fi link</li>
      </ul>
      <p>
        Umami doesn't use cookies and doesn't store your IP address. To tell visitors apart, it uses a one-way code made
        from your IP address, your browser, and a value that changes every day, so nobody (including us) can tell who
        you are or connect your visits across days. If your browser sends a “Do Not Track” signal, nothing is recorded.
      </p>

      <H2>Your IP address</H2>
      <p>
        Your IP address reaches our server with every request, as it does for any website. To stop abuse, the server
        keeps a count of recent uploads per IP address in memory and forgets it within an hour. We don't keep logs of
        IP addresses.
      </p>

      <H2>Settings saved in your browser</H2>
      <p>
        Your light or dark theme choice and whether you've dismissed the Ko-fi message are saved in your browser's local
        storage. They stay on your device and are never sent to us.
      </p>

      <H2>Where your data is processed</H2>
      <p>
        Our server is hosted by Hetzner in Ashburn, Virginia, USA. If you live elsewhere, your photo and visit data are
        processed there. Hetzner provides the server only and processes data on our behalf.
      </p>
      <p>
        Every visit passes through <a href="https://www.cloudflare.com/privacypolicy/" target="_blank" rel="noopener">Cloudflare</a>,
        which protects the server from attacks and speeds up the site. Cloudflare sees your IP address and the pages you
        request, as the server does, and processes them on our behalf. If it needs to check that you're not a bot, it
        may set a short-lived security cookie.
      </p>
      <p>
        We don't use any other services on this site: no ads, no social media widgets, and no third-party fonts or
        scripts. If you follow a link to <a href={SITE.donateUrl} target="_blank" rel="noopener">Ko-fi</a>, you leave
        this site, and Ko-fi's privacy policy applies there.
      </p>

      <H2>Legal basis (EU and UK visitors)</H2>
      <p>
        We process your photo to provide the template you asked for. We count visits and limit uploads per IP address
        because we have a legitimate interest in understanding how the site is used and keeping it running for
        everyone.
      </p>

      <H2>Your rights</H2>
      <p>
        Depending on where you live, you may have the right to access, correct, or delete your data, and to object to
        how it's used. Because we don't know who you are, we usually can't link any data to you, and your photo is
        deleted on its own within hours. For any request, write to <Contact />. You can also complain to your local data
        protection authority.
      </p>

      <H2>Children</H2>
      <p>
        {SITE.name} has no accounts and doesn't ask for personal information. If you're under 13, please ask a parent
        or guardian before using it, and only upload photos of objects.
      </p>

      <H2>Changes</H2>
      <p>
        If this policy changes, we'll update this page and the date at the top. See also the{" "}
        <a href={TERMS_PATH}>terms of use</a>.
      </p>
    </LegalPage>
  );
}

export function Terms() {
  return (
    <LegalPage title="Terms of use">
      <p>
        These terms cover your use of {SITE.name} (the website and the <a href={APP_PATH}>template maker</a>), run by{" "}
        {SITE.operator}. By using it, you agree to them.
      </p>

      <H2>The service</H2>
      <p>
        {SITE.name} turns a photo into a printable template for building a frame with a 3D pen. It's free to use. We
        may change, pause, or stop it at any time, and we may limit how much one person can use it so it stays fast for
        everyone.
      </p>

      <H2>Your photos</H2>
      <ul>
        <li>Only upload photos you have the right to use.</li>
        <li>
          You keep all rights to your photos. You let us process them only to make your template, as described in the{" "}
          <a href={PRIVACY_PATH}>privacy policy</a>.
        </li>
        <li>Don't upload anything illegal, or photos of people without their permission.</li>
      </ul>

      <H2>Your templates</H2>
      <p>
        The templates you make are yours. Use them, print them, and share or sell what you build with them however you
        like.
      </p>

      <H2>Fair use</H2>
      <p>
        Don't try to overload, break into, or get around the limits of the service, and don't use automated tools to
        send it large numbers of requests.
      </p>

      <H2>Safety</H2>
      <p>
        3D pens get hot and can burn. Follow your pen's instructions, work in a ventilated space, and supervise children.
        You're responsible for how you use your pen and materials.
      </p>

      <H2>Tips</H2>
      <p>
        Tips through Ko-fi are optional and help keep the site running. They don't buy any product, service, or perk,
        and Ko-fi's own terms apply to them.
      </p>

      <H2>No warranty</H2>
      <p>
        {SITE.name} is provided “as is”, without warranties of any kind. Templates are estimated from a single photo, so
        they may not match the object exactly. Check the print scale before you build.
      </p>

      <H2>Limitation of liability</H2>
      <p>
        To the fullest extent the law allows, we're not liable for any indirect or consequential loss, or for any
        damage or injury that comes from using the site, its templates, or a 3D pen. Nothing in these terms limits
        rights you have under consumer protection laws that can't be waived.
      </p>

      <H2>Changes and governing law</H2>
      <p>
        We may update these terms. The date at the top shows the latest version, and using the site after a change
        means you accept it. These terms are governed by the laws of {SITE.governingLaw}.
      </p>

      <H2>Contact</H2>
      <p>
        Questions about these terms go to <Contact />.
      </p>
    </LegalPage>
  );
}
