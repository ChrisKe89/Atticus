# Page snapshot

```yaml
- generic [active] [ref=e1]:
  - banner [ref=e2]:
    - generic [ref=e3]:
      - link "A Atticus" [ref=e4] [cursor=pointer]:
        - /url: /
        - generic [ref=e5] [cursor=pointer]: A
        - generic [ref=e6] [cursor=pointer]: Atticus
      - navigation "Primary" [ref=e7]:
        - link "Chat" [ref=e8] [cursor=pointer]:
          - /url: /
        - link "Contact" [ref=e9] [cursor=pointer]:
          - /url: /contact
        - link "Apps" [ref=e10] [cursor=pointer]:
          - /url: /apps
      - link "Sign in" [ref=e12] [cursor=pointer]:
        - /url: /signin
  - main [ref=e13]:
    - generic [ref=e14]:
      - generic [ref=e15]:
        - paragraph [ref=e16]: Access
        - heading "Sign in to Atticus" [level=1] [ref=e17]
        - paragraph [ref=e18]: Use your company email to receive a secure, single-use magic link.
      - generic [ref=e19]:
        - generic [ref=e20]:
          - generic [ref=e21]: Work email
          - textbox "Work email" [ref=e22]
        - button "Email me a magic link" [ref=e23] [cursor=pointer]
      - paragraph [ref=e24]:
        - text: Need access? Contact an administrator or
        - link "submit a request" [ref=e25] [cursor=pointer]:
          - /url: /contact
        - text: .
  - alert [ref=e26]
```