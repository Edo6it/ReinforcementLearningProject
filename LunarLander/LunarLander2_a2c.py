import torch
import torch.optim as optim
import torch.nn as nn
import torch.nn.functional as F
import gymnasium as gym

import numpy as np
from collections import deque

class Actor(nn.Module):
    def __init__(self, input, output):
        super().__init__()
        self.model = nn.Sequential(
            nn.Linear(input, 64),
            nn.Tanh(),
            nn.Linear(64, 32),
            nn.Tanh(),
            nn.Linear(32, output),
            nn.Softmax()
        )

    def forward(self, X):
        return self.model(X)
    
class Critic(nn.Module):
    def __init__(self,input):
        super().__init__()
        self.model=nn.Sequential(
            nn.Linear(input,64),
            nn.Tanh(),
            nn.Linear(64,32),
            nn.Tanh(),
            nn.Linear(32,1),
            nn.Softmax()
        )

    def forward(self,x):
        return self.model(x)

def t(x): return torch.from_numpy(x).float()
    
def main():

    gamma=0.99
    ep_rewards = deque(maxlen=100)
    view_step=30
    best_score=-400
    actor_loss=0
    critic_loss=0
    
    env = gym.make("LunarLander-v2")

    state_num = env.observation_space.shape[0]
    action_num = env.action_space.n

    load_weights=True

    actor=Actor(state_num,action_num)
    critic=Critic(state_num)
    
    if(load_weights):
        #actor load model
        actor = Actor(state_num,action_num)
        adam_actor = torch.optim.Adam(actor.parameters(), lr=1e-3)
        checkpoint = torch.load('C:\\Users\\kaidoama\\Desktop\\mio\\Reinforcement Learning\\LunarLander\\actor_model.pth')
        actor.load_state_dict(checkpoint['actor_state_dict'])
        adam_actor.load_state_dict(checkpoint['adam_actor_state_dict'])
        j = checkpoint['step']
        actor_loss = checkpoint['loss_actor']
        best_score=checkpoint['best_score']

        #critic load model
        critic = Critic(state_num)
        adam_critic = torch.optim.Adam(critic.parameters(), lr=1e-3)
        checkpoint = torch.load('C:\\Users\\kaidoama\\Desktop\\mio\\Reinforcement Learning\\LunarLander\\critic_model.pth')
        critic.load_state_dict(checkpoint['critic_state_dict'])
        adam_critic.load_state_dict(checkpoint['adam_critic_state_dict'])
        j = checkpoint['step']
        critic_loss = checkpoint['loss_critic']

        #make other 1000 steps
        total_episode = j+4000
    else:
        total_episode = 100
        
        adam_actor = torch.optim.Adam(actor.parameters(), lr=1e-3)
        adam_critic = torch.optim.Adam(critic.parameters(), lr=1e-3)
    

    ep_rewards = deque(maxlen=10)
    for i in range(total_episode):
        done=False
        total_reward=0
        if i%view_step==0:
            env = gym.make("LunarLander-v2",render_mode="human")
        else:
            env = gym.make("LunarLander-v2")
        state=env.reset()
        
        
        while True:
            if(len(state)==2):
                probs=actor(t(state[0]))
                dist=torch.distributions.Categorical(probs=probs)
                action=dist.sample()
                next_state, reward, done, truncated, info = env.step(action.detach().data.numpy())
                #print(reward)
                #calculate advantage
                td_target = reward + gamma * critic(t(next_state)) * (1-done)
                advantage = td_target - critic(t(state[0]))
                total_reward += reward

                state = next_state

                #compute loss
                critic_loss = advantage.pow(2).mean()
                adam_critic.zero_grad()
                critic_loss.backward()
                adam_critic.step()

                actor_loss = -dist.log_prob(action)*advantage.detach()
                adam_actor.zero_grad()
                actor_loss.backward()
                adam_actor.step()
            else:
                probs=actor(t(state))
                dist=torch.distributions.Categorical(probs=probs)
                action=dist.sample()
                next_state, reward, done, truncated, info = env.step(action.detach().data.numpy())
                #print(reward)

                #calculate advantage
                td_target = reward + gamma * critic(t(next_state)) * (1-done)
                advantage = td_target - critic(t(state))
                
                total_reward += reward

                state = next_state

                #compute loss
                critic_loss = advantage.pow(2).mean()
                adam_critic.zero_grad()
                critic_loss.backward()
                adam_critic.step()

                actor_loss = -dist.log_prob(action)*advantage.detach()
                adam_actor.zero_grad()
                actor_loss.backward()
                adam_actor.step()
    
    
            if done:
                ep_rewards.append(total_reward)
                x=round(np.mean(ep_rewards), 3)
                if(x>best_score):
                    best_score=round(np.mean(ep_rewards), 3)
                    torch.save(
                        {'step': i,
                        'actor_state_dict': actor.state_dict(),
                        'adam_actor_state_dict': adam_actor.state_dict(),
                        'best_score':best_score,
                        'loss_actor': actor_loss},
	                    'C:\\Users\\kaidoama\\Desktop\\mio\\Reinforcement Learning\\LunarLander\\actor_model.pth'
                    )
                    torch.save(
                        {'step': i,
                        'critic_state_dict': critic.state_dict(),
                        'adam_critic_state_dict': adam_critic.state_dict(),
                        'loss_critic': critic_loss},
	                    'C:\\Users\\kaidoama\\Desktop\\mio\\Reinforcement Learning\\LunarLander\\critic_model.pth'
                    )
                
                
                if i % 10 == 0:
                    print("episode: {}\treward: {}".format(i, round(np.mean(ep_rewards), 3)))
                break

if __name__ == '__main__':
    main()