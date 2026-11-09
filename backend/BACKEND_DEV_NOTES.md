# Backend dev notes

## Authentification

FastAPI gère OAuth2
https://fastapi.tiangolo.com/tutorial/security/first-steps/#recap

sur une route, un depend sur un OAuth2PasswordBearer par exemple, documente
l'OAuth2 et swagger présente donc l'option d'authentification

OAuth2 specifie que pour le password flow, le username et le password
sont envoyés en form data et les champs doivent
s'appeler `username` et `password`

un autre champ `scope` peut être envoyé, typiquement pour les permissions.
Ce qu'on met dans scope est libre, implementation specific.

OAuth2PasswordRequestForm permet de récupérer ces paramêtre simplement

il faut ensuite retourner un JSON avec un access_token et un "token_type": "bearer"
